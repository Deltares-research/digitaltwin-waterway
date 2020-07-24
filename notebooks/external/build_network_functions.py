import logging
from tqdm.autonotebook import tqdm
from typing import Sequence

from shapely.geometry import Point, MultiPoint, LineString
import numpy as np
import geopandas as gpd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def nearest_line(point: Point, lines: Sequence[LineString]) -> (int, float):
    # Splitting the closest line at given point
    #
    # point: Shapely Point
    # lines: List of shapely LineString
    # returns: index of nearest line, distance to nearest line
    d = np.full((len(lines)), fill_value=np.nan)
    for ii in range(len(lines)):
        d[ii] = point.distance(lines[ii])
    return np.argmin(d), np.min(d)


def all_points_in_radius(point: Point, all_points: Sequence[Point], radius: float) -> Sequence[int]:
    # Find all points within radius, sorted by distance (lowest first)
    #
    # point: Shapely point
    # all_points: list of shapely points
    # radius: Search radius
    # returns: indices within radius
    d = np.full((len(all_points)), fill_value=np.nan)
    for ii in range(len(all_points)):
        d[ii] = point.distance(all_points[ii])

    # Find points in radius
    points_in_radius = np.where(d < radius)[0]

    # Sort points on shortest distance
    order = np.argsort(d[points_in_radius])
    points_in_radius = points_in_radius[order]

    return points_in_radius


def chainage_on_line(point: Point, line: LineString) -> float:
    # Find chainage of line closest to point
    # point: Shapely Point
    # lines: Shapely Polylines
    # return
    return line.project(point)


def cut(line: LineString, chainage: float) -> Sequence[LineString]:
    # Cuts a line in two at a distance from its starting point
    # point: Shapely Polyline
    # chainage: distance along line

    # if 0 or longer than line, return line
    if chainage <= 0.0 or chainage >= line.length:
        return [LineString(line)]
    
    # Loop through all vertices of the line. If a vertex is exactly the given chainage, than 
    # split at this vertex (include vertex in both new lines). For the first vertex which 
    # chainage is larger than the searches radius, we know that we just passed it. We split the
    # line here and add a new point to both lines on exactly this chainage
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == chainage:
            return [
                LineString(coords[:i + 1]),
                LineString(coords[i:])]
        if pd > chainage:
            cp = line.interpolate(chainage)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]


def update_id_in_dataframe_around_chainage(df: gpd.geodataframe, name_nearest_line, chainages: Sequence[float],
                                           new_branch_names: Sequence[str], new_node_names: Sequence[str],
                                           geotype: Sequence[str], node_start_columnname="StartJunctionId",
                                           node_end_columnname="EndJunctionId") -> gpd.geodataframe:
    """
    Split one LineString in the DataFrame at the given chainages
    This removes the given line and adds multiple shorter new lines.
    The names of branches and nodes are given by lists

    """
    section_old = df.loc[name_nearest_line]

    # Delete old branch
    df = df.drop(name_nearest_line, axis='index')

    chainages = sorted(chainages)
    chainages = np.hstack(
        (chainages[0], np.diff(chainages)))  # all but the first should be relative to the previous chainage
    splits = []
    remainder = section_old.geometry
    for chainage in chainages:
        s = cut(remainder, chainage)
        splits.append(s[0])
        remainder = s[1]
    splits.append(remainder)

    # Create new sections
    for ii, split in enumerate(splits):
        section_new = section_old.copy()
        section_new['geometry'] = split

        # Name the branch
        if geotype[ii] is not None:
            section_new['GeoType'] = geotype[ii]

        # Name the branch
        section_new.name = new_branch_names[ii]

        # Name the nodes
        if ii == 0:
            section_new[node_end_columnname] = new_node_names[ii]
        elif ii == (len(splits) - 1):
            section_new[node_start_columnname] = new_node_names[ii - 1]
        else:
            section_new[node_start_columnname] = new_node_names[ii - 1]
            section_new[node_end_columnname] = new_node_names[ii]

        # Update DataFrame
        df = df.append(section_new)

    return df


def update_id_in_dataframe_at_chainage(df: gpd.geodataframe, name_nearest_line, chainage: float, node_id,
                                       node_start_columnname="StartJunctionId",
                                       node_end_columnname="EndJunctionId") -> gpd.geodataframe:
    """
    Split one LineString in the DataFrame at the given chainage. This removes
    the given line and adds two shorter new lines.

    """
    section_old = df.loc[name_nearest_line]
    split = cut(section_old.geometry, chainage)

    # Create new sections
    section_new_1 = section_old.copy()
    section_new_2 = section_old.copy()

    section_new_1['geometry'] = split[0]
    section_new_2['geometry'] = split[1]

    section_new_1[node_end_columnname] = node_id
    section_new_2[node_start_columnname] = node_id

    # Set index
    section_new_1.name = f'{section_old.name}_A'
    section_new_2.name = f'{section_old.name}_B'

    # Update DataFrame
    df = df.drop(section_old.name, axis='index')
    df = df.append(section_new_1)
    df = df.append(section_new_2)

    return df


def create_nodes_from_geodataframe(all_nodes: Sequence, fairway: gpd.geodataframe,
                                   node_start_columnname="StartJunctionId",
                                   node_end_columnname="EndJunctionId") -> gpd.geoseries:
    """
    For each node, find all fairways that have this node as start or end point.
    Get the average location of these locations

    all_nodes: list of all nodes to find coordinate
    fairway: geodataframe containing linestrings with start/end point of nodes

    return: GeoSeries
    """

    fairway_nodes = {}
    for n in all_nodes:
        nn = fairway[fairway[node_start_columnname] == n]['geometry']
        points_start = [geom.coords[0] for geom in nn.geometry.values]
        nn = fairway[fairway[node_end_columnname] == n]['geometry']
        points_end = [geom.coords[-1] for geom in nn.geometry.values]

        points = MultiPoint(points_start + points_end)
        centroid = points.centroid

        fairway_nodes[n] = centroid
    fairway_nodes = gpd.GeoSeries(fairway_nodes)
    return fairway_nodes


def group_subobjects(objects: gpd.geodataframe, fieldname=None, type_selection='max'):
    """
    The netwerk only allows one object per location. For locks and bridges that means we limit the number of openings and locks to one (for now).
    This script tries to take the most governing object. For bridges for example, the highest HeightClosed.

    TODO: Keep the count of number of locks

    """

    if fieldname is not None:
        # Remove nans
        objects = objects[~objects[fieldname].isna()]

    # Only keep opening with the maximum [fieldname]
    if type_selection == 'max':
        ii = objects.groupby('Id')[fieldname].idxmax().values

        objects = objects.reindex(ii)
        objects = objects.set_index('Id')
    else:
        print('Unknown criteria')

    return objects


def split_lines_around_points(branches: gpd.geodataframe, objects: gpd.geodataframe, max_distance=0.002, prefix='B',
                              geotype='bridge', dx=0.0001) -> gpd.geodataframe:
    """
    branches: geodataframe of polylines
    objects: geodataframe of points where you want to polylines to split

    max_distance: maximum distance of point to line in order. When max_distance is exceeded, the point will be ignored
    prefix: the nodes will be split get a new of the index of 'bridge_selection' with this prefix

    node_start_columnname: in dataframe 'section_selection' name of start_node
    node_end_columnname: in dataframe 'section_selection' name of end_node

    # TODO: Convert to RD? or compute length in lat-lon for bridge/locks
    """

    branches_with_objects = branches.copy()

    for k, obj in tqdm(objects.iterrows(), total=objects.shape[0]):

        b = obj.geometry  # abreviate
        object_id = f'{prefix}{k}'

        # Split closest section
        nearest_section, distance_to_nearest_section = nearest_line(b, branches_with_objects.geometry.values)
        name_nearest_section = branches_with_objects.index[nearest_section]

        geometry_nearest_line = branches_with_objects.loc[name_nearest_section].geometry

        if distance_to_nearest_section > max_distance:  # If distance (in degree) it too large, apparently it's not near a section
            logger.debug(f'Too far from river, ignoring point (name: "{obj.Name}")')
            continue

        chainage = chainage_on_line(b, geometry_nearest_line)

        clips_to_startpoint = chainage - dx / 2 <= 0
        clips_to_endpoint = chainage + dx / 2 >= geometry_nearest_line.length
        if clips_to_startpoint:
            chainage_2 = dx
            if chainage_2 > geometry_nearest_line.length:
                # Rename branch to bridge
                branches_with_objects.loc[name_nearest_section, 'GeoType'] = geotype
                branches_with_objects.loc[name_nearest_section].name = object_id
                continue
            chainages = [chainage_2]
            new_branch_names = [object_id, name_nearest_section]
            geotype_names = [geotype, None]
            new_node_names = [f'{object_id}_A']
        elif clips_to_endpoint:
            chainage_2 = geometry_nearest_line.length - dx
            if chainage_2 < 0:
                # Rename branch to bridge
                branches_with_objects.loc[name_nearest_section, 'GeoType'] = geotype
                branches_with_objects.loc[name_nearest_section].name = object_id
                continue
            chainages = [chainage_2]
            new_branch_names = [name_nearest_section, object_id]
            geotype_names = [None, geotype]
            new_node_names = [f'{object_id}_A']
        else:
            chainage_1 = chainage - dx / 2
            chainage_2 = chainage + dx / 2
            chainages = [chainage_1, chainage_2]
            new_branch_names = [f'{name_nearest_section}_A', object_id, f'{name_nearest_section}_B']
            geotype_names = [None, geotype, None]
            new_node_names = [f'{object_id}_A', f'{object_id}_B']

        branches_with_objects = update_id_in_dataframe_around_chainage(branches_with_objects,
                                                                       name_nearest_section, chainages,
                                                                       new_branch_names, new_node_names,
                                                                       geotype=geotype_names)
    return branches_with_objects


def split_lines_at_points(branches: gpd.geodataframe, objects: gpd.geodataframe, max_distance=0.002, prefix='B',
                          node_start_columnname="StartJunctionId",
                          node_end_columnname="EndJunctionId") -> gpd.geodataframe:
    """
    section_selection: geodataframe of polylines
    bridges_selection: geodataframe of points where you want to polylines to split

    max_distance: maximum distance of point to line in order. When max_distance is exceeded, the point will be ignored
    prefix: the nodes will be split get a new of the index of 'bridge_selection' with this prefix

    node_start_columnname: in dataframe 'section_selection' name of start_node
    node_end_columnname: in dataframe 'section_selection' name of end_node

    """

    branches_with_objects = branches.copy()

    for k, obj in tqdm(objects.iterrows(), total=objects.shape[0]):

        b = obj.geometry  # abreviate
        object_id = f'{prefix}{k}'

        # Split closest section
        nearest_section, distance_to_nearest_section = nearest_line(b, branches_with_objects.geometry.values)
        name_nearest_section = branches_with_objects.index[nearest_section]
        geometry_nearest_line = branches_with_objects.loc[name_nearest_section].geometry

        if distance_to_nearest_section > max_distance:  # If distance (in degree) it too large, apparently it's not near a section
            logger.debug(f'Too far from river, ignoring point (name: "{obj.Name}")')
            continue

        chainage = chainage_on_line(b, geometry_nearest_line)
        clips_to_startpoint = chainage == 0
        clips_to_endpoint = abs(geometry_nearest_line.length - chainage) < 1e-10

        # Chainage already on a node, no need to split
        if clips_to_startpoint or clips_to_endpoint:

            # Replace name of node, with name of bridge
            if clips_to_startpoint:
                node_id = branches_with_objects.loc[name_nearest_section, node_start_columnname]
            else:
                node_id = branches_with_objects.loc[name_nearest_section, node_end_columnname]

            logger.debug(f'Renaming node {node_id} to point {object_id} (name: "{obj.Name}")')
            branches_with_objects[[node_start_columnname, node_end_columnname]] = \
                branches_with_objects[[node_start_columnname, node_end_columnname]].replace({node_id: object_id})
            continue

        branches_with_objects = update_id_in_dataframe_at_chainage(branches_with_objects,
                                                                   name_nearest_section, chainage, object_id)

    return branches_with_objects


def find_crossings_in_branches(branches, max_distance=0.005, prefix='FN', node_start_columnname="StartJunctionId",
                               node_end_columnname="EndJunctionId"):
    """
    For a geopandas of branches, the connectivity for a network is computed. This connectivity is stored in columnnames
    of the start node and end node.

    Basicly two actions are performed:
    - When start/end points are close together, they are given the same node_id.
    - When a start/end point is close to the continuous part of a second branch, split this second branch at this location.

    :param branches: geopandas of all branches
    :param max_distance: max distance to snap and split to
    :param prefix: prefix to node ID's
    :param node_start_columnname: name of column to store startnode
    :param node_end_columnname: name of column to store endnode
    :return:
    """

    # Create empty columns
    branches.loc[:, node_start_columnname] = None
    branches.loc[:, node_end_columnname] = None

    # Generator for node_id names
    generate_node_id = (f'{prefix}{ii}' for ii in range(999999))

    i_row = 0
    while i_row < branches.shape[0]:  # Cannot loop over it, because it's changing shape when splitting
        ii = branches.index[i_row]
        i_row += 1

        logger.debug(f'Fairway index {ii}')

        # Process both start and end point
        startpoint = Point(branches.loc[ii].geometry.coords[0])
        endpoint = Point(branches.loc[ii].geometry.coords[-1])

        for point, columnname in zip([startpoint, endpoint],
                                     [node_start_columnname, node_end_columnname]):

            # Check if this is already has an id (than it is a split version of a branch we already did)
            if branches.loc[ii][columnname] is not None:
                continue

            logger.debug(f'  {columnname[:-10]}')

            subset_fairways = branches.drop(ii)  # All fairways except the current
            all_startpoints = [Point(geom.coords[0]) for geom in subset_fairways.geometry.values]
            all_endpoints = [Point(geom.coords[-1]) for geom in subset_fairways.geometry.values]
            all_points = (all_startpoints + all_endpoints)

            # Find all nearby points within radius
            i_nearby_points = all_points_in_radius(point, all_points, radius=max_distance)

            node_id = next(generate_node_id)
            snap_fairways = []

            for i_nearby_point in i_nearby_points:
                if i_nearby_point < subset_fairways.shape[0]:
                    snap_to_fairway = subset_fairways.iloc[i_nearby_point].name
                    snap_column = node_start_columnname
                else:
                    snap_to_fairway = subset_fairways.iloc[i_nearby_point - subset_fairways.shape[0]].name
                    snap_column = node_end_columnname

                snap_node_name = branches.loc[snap_to_fairway, snap_column]
                if snap_node_name is not None:
                    node_id = snap_node_name  # Take name of snap_node instead

                snap_fairways.append(snap_to_fairway)  # Create list for later on

            logger.debug(f'    nearby points: {snap_fairways}')

            branches.loc[ii, columnname] = node_id

            # also remove the fairways which are snapping to nodes already
            subset_subset_fairways = subset_fairways.drop(snap_fairways)

            # Find all nearby lines
            i_nearest_line, distance_nearest_line = nearest_line(point, subset_subset_fairways.geometry.values)
            name_nearest_line = subset_subset_fairways.index[i_nearest_line]

            if distance_nearest_line > max_distance:
                logger.debug('    No nearby branch')
            else:
                logger.debug(f'    Nearest branch: {name_nearest_line}')
                # Find location of intersection and split geometry in two geometries
                geometry_nearest_line = branches.loc[name_nearest_line].geometry
                chainage = chainage_on_line(point, geometry_nearest_line)

                clips_to_startpoint = chainage == 0
                clips_to_endpoint = abs(geometry_nearest_line.length - chainage) < 1e-10

                if clips_to_startpoint or clips_to_endpoint:
                    logger.debug('      Already a node, so not splitting')
                    continue
                else:
                    logger.debug('      Splitting fairway at node')

                    # Only continue to next index if we did not just delete a branch that we already processed.
                    if np.where(branches.index == name_nearest_line)[0][0] < i_row:
                        i_row += -1

                    branches = update_id_in_dataframe_at_chainage(branches, name_nearest_line, chainage, node_id)

    return branches
