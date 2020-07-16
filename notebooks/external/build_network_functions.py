import logging
from pathlib import Path
from tqdm import tqdm_notebook as tqdm

import json
import geojson
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPoint, Polygon, MultiPolygon, LineString
import numpy as np
import pandas as pd
import geopandas as gpd


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Splitting the closest line at given point

def nearest_line(point, lines):
    # Returns index of the closest line to the point
    # point: Shapely Point
    # lines: List of shapely Polylines
    # returns: index of nearest line, distance to nearest line
    d = np.full((len(lines)), fill_value=np.nan)
    for ii in range(len(lines)):
        d[ii] = point.distance(lines[ii])
    return np.argmin(d), np.min(d)


def all_points_in_radius(point, all_points, radius):
    # Find all points within radius
    # point: Shapely point
    # all_points: list of shapely points
    # returns: indices within radius
    d = np.full((len(all_points)), fill_value=np.nan)
    for ii in range(len(all_points)):
        d[ii] = point.distance(all_points[ii])
    return np.where(d < radius)[0]


def chainage_on_line(point, line):
    # Find chainage of line closest to point
    # point: Shapely Point
    # lines: Shapely Polylines
    return line.project(point)


def cut(line, chainage):
    # Cuts a line in two at a distance from its starting point
    # point: Shapely Polyline
    # chainage: distance along line

    # if 0 or longer than line, return line
    if chainage <= 0.0 or chainage >= line.length:
        return [LineString(line)]
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


def update_id_in_dataFrame_at_chainage(df, name_nearest_line, chainage, node_ID,
                                       node_start_columnname="StartJunctionId", node_end_columnname="EndJunctionId"):
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

    section_new_1[node_end_columnname] = node_ID
    section_new_2[node_start_columnname] = node_ID

    # Set index
    section_new_1.name = f'{section_old.name}_A'
    section_new_2.name = f'{section_old.name}_B'

    # Update DataFrame
    df = df.drop(section_old.name, axis='index')
    df = df.append(section_new_1)
    df = df.append(section_new_2)

    return df



def create_nodes_from_GeoDataFrame(all_nodes, fairway,node_start_columnname="StartJunctionId",
                                           node_end_columnname="EndJunctionId"):
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


def group_subobjects(objects, fieldname=None, type_selection='max'):
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





def update_id_in_dataFrame_around_chainage(df, name_nearest_line, chainages, new_branch_names, new_node_names, geotype,
                              node_start_columnname="StartJunctionId", node_end_columnname="EndJunctionId"):
    """
    Split one LineString in the DataFrame at the given chainages
    This removes the given line and adds multiple shorter new lines. The middle section will get properties of the element


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


def split_lines_around_points(branches, objects, max_distance=0.002, prefix='B', geotype='bridge',
                              dx=0.0001,
                              node_start_columnname="StartJunctionId", node_end_columnname="EndJunctionId"):
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

    for k, object in tqdm(objects.iterrows(), total=objects.shape[0]):

        b = object.geometry  # abreviate
        object_ID = f'{prefix}{k}'

        # Split closest section
        nearest_section, distance_to_nearest_section = nearest_line(b, branches_with_objects.geometry.values)
        name_nearest_section = branches_with_objects.index[nearest_section]

        geometry_nearest_line = branches_with_objects.loc[name_nearest_section].geometry

        if distance_to_nearest_section > max_distance:  # If distance (in degree) it too large, apparently it's not near a section
            logger.debug(f'Too far from river, ignoring point (name: "{object.Name}")')
            continue

        chainage = chainage_on_line(b, geometry_nearest_line)

        clips_to_startpoint = chainage - dx / 2 <= 0
        clips_to_endpoint = chainage + dx / 2 >= geometry_nearest_line.length
        if clips_to_startpoint:
            chainage_2 = dx
            if chainage_2 > geometry_nearest_line.length:
                # Rename branch to bridge
                branches_with_objects.loc[name_nearest_section, 'GeoType'] = geotype
                branches_with_objects.loc[name_nearest_section].name = object_ID
                continue
            chainages = [chainage_2]
            new_branch_names = [object_ID, name_nearest_section]
            geotype_names = [geotype, None]
            new_node_names = [f'{object_ID}_A']
        elif clips_to_endpoint:
            chainage_2 = geometry_nearest_line.length - dx
            if chainage_2 < 0:
                # Rename branch to bridge
                branches_with_objects.loc[name_nearest_section, 'GeoType'] = geotype
                branches_with_objects.loc[name_nearest_section].name = object_ID
                continue
            chainages = [chainage_2]
            new_branch_names = [name_nearest_section, object_ID]
            geotype_names = [None, geotype]
            new_node_names = [f'{object_ID}_A']
        else:
            chainage_1 = chainage - dx / 2
            chainage_2 = chainage + dx / 2
            chainages = [chainage_1, chainage_2]
            new_branch_names = [f'{name_nearest_section}_A', object_ID, f'{name_nearest_section}_B']
            geotype_names = [None, geotype, None]
            new_node_names = [f'{object_ID}_A', f'{object_ID}_B']

        branches_with_objects = update_id_in_dataFrame_around_chainage(branches_with_objects,
                                                                                name_nearest_section, chainages,
                                                                                new_branch_names, new_node_names,
                                                                                geotype=geotype_names)
    return branches_with_objects

def split_lines_at_points(branches, objects, max_distance=0.002, prefix='B',
                          node_start_columnname="StartJunctionId", node_end_columnname="EndJunctionId"):
    """
    section_selection: geodataframe of polylines
    bridges_selection: geodataframe of points where you want to polylines to split

    max_distance: maximum distance of point to line in order. When max_distance is exceeded, the point will be ignored
    prefix: the nodes will be split get a new of the index of 'bridge_selection' with this prefix

    node_start_columnname: in dataframe 'section_selection' name of start_node
    node_end_columnname: in dataframe 'section_selection' name of end_node

    """

    branches_with_objects = branches.copy()

    for k, object in tqdm(objects.iterrows(), total=objects.shape[0]):

        b = object.geometry  # abreviate
        object_ID = f'{prefix}{k}'

        # Split closest section
        nearest_section, distance_to_nearest_section = nearest_line(b, branches_with_objects.geometry.values)
        name_nearest_section = branches_with_objects.index[nearest_section]
        geometry_nearest_line = branches_with_objects.loc[name_nearest_section].geometry

        if distance_to_nearest_section > max_distance:  # If distance (in degree) it too large, apparently it's not near a section
            logger.debug(f'Too far from river, ignoring point (name: "{object.Name}")')
            continue

        chainage = chainage_on_line(b, geometry_nearest_line)
        clips_to_startpoint = chainage == 0
        clips_to_endpoint = abs(geometry_nearest_line.length - chainage) < 1e-10

        # Chainage already on a node, no need to split
        if clips_to_startpoint or clips_to_endpoint:

            # Replace name of node, with name of bridge
            if clips_to_startpoint:
                node_ID = branches_with_objects.loc[name_nearest_section, node_start_columnname]
            else:
                node_ID = branches_with_objects.loc[name_nearest_section, node_end_columnname]

            logger.debug(f'Renaming node {node_ID} to point {object_ID} (name: "{object.Name}")')
            branches_with_objects[[node_start_columnname, node_end_columnname]] = \
            branches_with_objects[[node_start_columnname, node_end_columnname]].replace({node_ID: object_ID})
            continue

        branches_with_objects = update_id_in_dataFrame_at_chainage(branches_with_objects,
                                                                            name_nearest_section, chainage, object_ID)

    return branches_with_objects