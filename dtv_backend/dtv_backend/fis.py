"""
Utilities to work with the Fairway Information System (FIS) network.
"""
import functools
import io
import itertools
import logging
import pathlib
import re
import tempfile
import urllib
import json
import pickle

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pyproj
import requests
import requests_cache
import scipy.interpolate
import shapely
import shapely.geometry
import shapely.wkt
from pandas.api.types import CategoricalDtype


import dtv_backend


# cache all http requests for stability and performance
requests_cache.install_cache("requests_cache")

# add pairwise to itertools for python < 3.10
if not hasattr(itertools, "pairwise"):

    def pairwise(iterable):
        # pairwise('ABCDEFG') --> AB BC CD DE EF FG
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    itertools.pairwise = pairwise


logger = logging.getLogger(__name__)

package_path = pathlib.Path(__file__).parent.parent

# define the coorinate system
geod = pyproj.Geod(ellps="WGS84")


# The network version 0.1 contains the lat/lon distance in a length property.
# But we need the "great circle" or projected distance.
# Let's define a function to recompute it.
def edge_length(edge):
    """
    Compute the great circle length of an edge.
    
    Parameters
    ----------
    edge : dict
        An edge from the networkx graph.
    
    Returns
    -------
    distance : float
        The length of the edge in meters.

    """
    # get the geometry
    geom = edge["geometry"]
    # get lon, lat
    lats, lons = geom.xy
    distance = geod.line_length(lons, lats)
    return distance


# now create the function can load the network


# store the result so it will immediately give a result
@functools.lru_cache(maxsize=100)
def load_fis_network(url):
    """
    Load the topological fairway information system network.
    
    Parameters
    ----------
    maxsize : int
        The maximum size of the cache.
    """
    # TODO: check for local location
    data_dir = "~/data/river/dtv/fis/0.3/network_digital_twin_v0.3.pickle"
    data_path = pathlib.Path(data_dir).expanduser()
    if data_path.exists():
        filename = str(data_path)
        n_bytes = data_path.stat().st_size
        with open(filename, "rb") as file:
            G = pickle.load(file)
    else:
        # get the data from the url
        resp = requests.get(url)
        # convert to file object
        stream = io.StringIO(resp.text)

        # create a temporary file
        f = tempfile.NamedTemporaryFile()
        f.close()

        # retrieve the info and create the graph
        urllib.request.urlretrieve(url, f.name)
        # This will take a minute or two
        # Here we convert the network to a networkx object
        with open(f.name, "rb") as file:
            G = pickle.load(file)

        # the temp file can be deleted
        del f
        # some brief info
        n_bytes = len(resp.content)

    msg = """Loaded network from {url} file size {mb:.2f}MB. Network has {n_nodes} nodes and {n_edges} edges."""
    summary = msg.format(
        url=url, mb=n_bytes / 1000**2, n_edges=len(G.edges), n_nodes=len(G.nodes)
    )
    logger.info(summary)

    # The topological network contains information about the original geometry.
    # Let's convert those into python shapely objects for easier use later
    for n in G.nodes:
        G.nodes[n]["geometry"] = shapely.geometry.Point(
            G.nodes[n]["X"], G.nodes[n]["Y"]
        )
        G.nodes[n]["n"] = n
    for e in G.edges:
        edge = G.edges[e]
        edge["geometry"] = shapely.wkt.loads(edge["Wkt"])
        edge["length"] = edge_length(edge)

    return G


def find_closest_node(G, point):
    """
    Find the node on graph G that is closest to the given
    shapely.geometry.Point point

    Parameters
    ----------
    G : networkx.Graph
        The graph in which the closest node is to be found.
    point : shapely.geometry.Point
        The point for which the closest node is to be found.

    Returns
    -------
    name_node : str
        The name of the closest node.
    distance_node : float
        The distance to the closest node.

    """
    distance = np.full((len(G.nodes)), fill_value=np.nan)
    for ii, n in enumerate(G.nodes):
        distance[ii] = point.distance(G.nodes[n]["geometry"])
    name_node = list(G.nodes)[np.argmin(distance)]
    distance_node = np.min(distance)
    return name_node, distance_node


def find_closest_edge(G, point):
    """
    Find the edge on graph G that is closest to the given.

    Parameters
    ----------
    G : networkx.Graph
        The graph in which the closest edge is to be found.
    point : shapely.geometry.Point
        The point for which the closest edge is to be found.

    Returns
    -------
    name_edge : str
        The name of the closest edge.
    distance_edge : float
        The distance to the closest edge.

    """

    distance = np.full((len(G.edges)), fill_value=np.nan)
    for ii, e in enumerate(G.edges):
        # start_node = G.nodes[G.edges[e]['StartJunctionId']]
        # end_node = G.nodes[G.edges[e]['EndJunctionId']]
        # distance[ii] = point.distance()
        distance[ii] = point.hausdorff_distance(shapely.wkt.loads(G.edges[e]["Wkt"]))
    name_edge = list(G.edges)[np.argmin(distance)]
    distance_edge = np.min(distance)
    return name_edge, distance_edge


def determine_max_draught_on_path(
    graph, origin, destination, lobith_discharge, underkeel_clearance=0.30, default=100
):
    """
    Compute the max draught on the route. If none of the locations where we know the
    discharge depth relation is on the route, return the default max_draught.

    Parameters
    ----------
    graph : networkx.Graph
        The FIS network graph.
    origin : shapely.geometry.Point
        The origin point.
    destination : shapely.geometry.Point
        The destination point.
    lobith_discharge : float
        The discharge at Lobith in m3/s.
    underkeel_clearance : float, optional
        The underkeel clearance in meters. The default is 0.30.
    default : float, optional
        The default max draught in meters. The default is 100.

    Returns
    -------
    max_draught : float
        The maximum draught on the route in meters.

    """
    # TODO: the file "depth.csv" is missing... this should be loaded as discharge_df

    # if cache.get((origin.geometry, destination.geometry, lobith_discharge)):
    #     return cache.get((origin.geometry, destination.geometry, lobith_discharge))

    depth_path = package_path / "data" / "depth.csv"
    discharge_df = pd.read_csv(depth_path)

    # also return distance
    origin_node, _ = find_closest_node(graph, origin.geometry)
    destination_node, _ = find_closest_node(graph, destination.geometry)

    # determine path and route (subgraph)
    path = nx.dijkstra_path(graph, origin_node, destination_node, weight="Length")
    route = nx.DiGraph(graph.subgraph(path))

    # get the discharge interpolation functions
    discharge_df = discharge_df.rename(columns={"Unnamed: 0": "Lobith"})
    discharge_df = discharge_df.set_index("Lobith")
    F = discharge_df.apply(
        lambda series: scipy.interpolate.interp1d(series.index, series.values)
    )

    # add some coordinates
    coordinates = {
        "Kaub": shapely.geometry.Point(7.764967, 50.085433),
        "Duisburg-Ruhrort": shapely.geometry.Point(6.727933, 51.455350),
        "Emmerich": shapely.geometry.Point(6.245600, 51.829250),
        "Erlecom": shapely.geometry.Point(5.95044, 51.86054),
        "Nijmegen": shapely.geometry.Point(5.84601, 51.85651),
        "Ophemert": shapely.geometry.Point(5.41371, 51.85023),
        "St. Andries": shapely.geometry.Point(5.33567, 51.80930),
        "Zaltbommel": shapely.geometry.Point(5.24990, 51.81733),
        "Nijmegen (fixed layer)": shapely.geometry.Point(5.85458, 51.85264),
    }
    # store in a DataFrame
    depth_df = pd.DataFrame(F, columns=["F"])
    # add the geometry
    depth_locations_df = pd.DataFrame(
        data=coordinates.items(), columns=["location", "geometry"]
    ).set_index("location")
    # merge back together
    depth_df = pd.merge(depth_df, depth_locations_df, left_index=True, right_index=True)

    # lookup closest locations
    location_edge = {}
    for name, row in depth_df.iterrows():
        location_edge[name] = find_closest_edge(graph, row.geometry)[0]
    # merge closest edges with the table
    edges_df = pd.DataFrame(location_edge).T.rename(
        columns={0: "edge_from", 1: "edge_to"}
    )
    depth_df = pd.merge(depth_df, edges_df, left_index=True, right_index=True)
    depth_df["on_route"] = depth_df.apply(
        lambda x: route.has_edge(x.edge_from, x.edge_to), axis=1
    )

    # determine the minimal depth
    min_depth = (
        depth_df[depth_df.on_route].apply(lambda x: x.F(lobith_discharge), axis=1).min()
    )

    if not min_depth.any():
        max_draught = default
    else:
        max_draught = min_depth - underkeel_clearance

    # assume graph stays the same
    cache[(origin.geometry, destination.geometry, lobith_discharge)] = max_draught

    return max_draught


def determine_max_height_on_path(graph, origin, destination, lobith_discharge):
    """
    Dummy function to determine max height on the path.

    Returns
    -------
    6 : int
        Dummy value for max height.
    """
    return 6


def determine_max_layers(height):
    """
    Determine max number of container layers as a function of available height 
    on the route.
    
    Parameters
    ----------
    height : float
        The available height in meters.

    Returns
    -------
    max_layers : int
        The maximum number of container layers.
        
    """

    container_height = 2.591

    max_layers = 0
    if height <= 5.8:
        max_layers = 2
    elif height <= 8.5:
        max_layers = 2
    elif height <= 11.05:
        max_layers = 3
    else:
        max_layers = 4

    return max_layers


def shorted_path_by_dimensions(
    graph, source, destination, width, height, depth, length
):
    """
    Create a new constrained graph, based on dimensions, of the same type as 
    graph and find the shortest path.
    
    Parameters
    ----------
    graph : networkx.Graph
        The original graph.
    source : str
        The source node.
    destination : str
        The destination node.
    width : float
        The minimum width in meters.
    height : float
        The minimum height in meters.
    depth : float
        The minimum depth in meters.
    length : float
        The minimum length in meters.

    Returns
    -------
    path : list
        The shortest path as a list of nodes.

    """
    nodes = []
    edges = []
    for start_node, end_node, edge in graph.edges(data=True):
        # GeneralWidth can be missing or None or it should be bigger than width
        width_ok = (
            "GeneralWidth" not in edge
            or np.isnan(edge["GeneralWidth"])
            or edge["GeneralWidth"] >= width
        )
        height_ok = (
            "GeneralHeight" not in edge
            or np.isnan(edge["GeneralHeight"])
            or edge["GeneralHeight"] >= height
        )
        depth_ok = (
            "GeneralDepth" not in edge
            or edge["GeneralDepth"] >= depth
            or np.isnan(edge["GeneralDepth"])
        )
        length_ok = (
            "GeneralLength" not in edge
            or edge["GeneralLength"] >= length
            or np.isnan(edge["GeneralLength"])
        )
        if all([width_ok, height_ok, depth_ok, length_ok]):
            edges.append((start_node, end_node))
            nodes.append(start_node)
            nodes.append(end_node)

    constrained_graph = graph.__class__()

    for node in nodes:
        constrained_graph.add_node(node)
    for edge in edges:
        constrained_graph.add_edge(edge[0], edge[1])

    path = shorted_path(
        graph=constrained_graph,
        source=source,
        destination=destination,
        weight="length_m",
    )
    return path


def shorted_path(graph, source, destination, weight="length_m"):
    """
    Compute shortest path on a graph.
    
    Parameters
    ----------
    graph : networkx.Graph
        The graph on which to compute the shortest path.
    source : str
        The source node.
    destination : str
        The destination node.
    weight : str, optional
        The edge attribute to use as weight. The default is "length_m".
        
    Returns
    -------
    path : list
        The shortest path as a list of nodes.
    """
    path = nx.dijkstra_path(graph, source, destination, weight=weight)
    return path


def compute_path_length(graph, path, key="length_m"):
    """
    Auxiliary function to compute distance of a path.
    
    Parameters
    ----------
    graph : networkx.Graph
        The graph on which to compute the path length.
    path : list
        The path as a list of nodes.
    key : str, optional
        The edge attribute to use as length. The default is "length_m".

    Returns
    -------
    total_distance : float
        The total distance of the path.
    
    """
    total_distance = 0
    for e in zip(path[:-1], path[1:]):
        edge_distance = graph.edges[e][key]
        total_distance += edge_distance
    return total_distance


def extract_structure(e):
    """
    Extract structure information from edge tuple.
    
    Parameters
    ----------
    e : tuple
        The edge as a tuple of (source, target).

    Returns
    -------
    match : dict or None
        The structure information as a dictionary or None if no structure is found.

    """
    structure_re = re.compile("^(?P<structure_code>[SLB])(?P<structure_id>\d+)_[AB]$")

    structure_types = {"S": "Structure", "L": "Lock", "B": "Bridge"}
    source_match = structure_re.match(e[0])
    target_match = structure_re.match(e[1])
    if not source_match or not target_match:
        return None

    # check if we have the same structure
    source_match = source_match.groupdict()
    target_match = target_match.groupdict()
    # different structures
    if source_match["structure_code"] != target_match["structure_code"]:
        return None
    if source_match["structure_id"] != target_match["structure_id"]:
        return None

    match = source_match
    match["structure_type"] = structure_types[match["structure_code"]]
    return match


def make_route_gdf(waypoints, network):
    """
    Compute a route and return a geopandas dataframe with the route.
    
    Parameters
    ----------
    waypoints : list
        A list of waypoints as node ids.
    network : networkx.Graph
        The network on which to compute the route.

    Returns
    -------
    route_gdf : geopandas.GeoDataFrame
        A geopandas dataframe with the route.

    """
    assert len(waypoints) > 0, "there should be at least 1 waypoint"
    route = []
    for segment_i, (source, target) in enumerate(itertools.pairwise(waypoints)):
        sub_route = nx.shortest_path(
            network, source=source, target=target, weight="length_m"
        )
        # TODO: Do we need to add the final point?
        edges = itertools.chain(
            itertools.pairwise(sub_route), [(sub_route[-1], sub_route[-1])]
        )
        for step_i, (n, e) in enumerate(zip(sub_route, edges)):

            is_stop = e[0] == e[1]

            # we are not moving
            geometry = network.nodes[n]["geometry"]
            length_m = 0

            if not is_stop:
                # get length if we have an edge
                length_m = network.edges[e]["length_m"]
                geometry = network.edges[e]["geometry"]

            row = {
                # sub segment
                "segment": segment_i,
                # step in segement
                "step": step_i,
                # start node id
                "n": n,
                # edge id
                "e": e,
                # are we stopping at this node
                "is_stop": is_stop,
                # soure of segment
                "source": source,
                # target of segment
                "target": target,
                # length of edge
                "length_m": length_m,
                # structure on edge
                "structure": extract_structure(e),
                # edge geometry
                "geometry": geometry,
            }
            route.append(row)
    route_gdf = gpd.GeoDataFrame(route)
    route_gdf["length_m_cumsum"] = route_gdf["length_m"].cumsum()
    return route_gdf


def route_metadata(route_gdf, network):
    """
    Compute metadata for the route
    
    Parameters
    ----------
    route_gdf : geopandas.GeoDataFrame
        The route as a geopandas dataframe.
    network : networkx.Graph
        The network on which to compute the route.

    Returns
    -------
    dict
        Metadata about the route.
    """
    total_length_m = route_gdf["length_m"].sum()
    n_edges = route_gdf[~route_gdf.is_stop].shape[0]
    n_nodes = n_edges + 1
    source_n = route_gdf["n"].iloc[0]
    target_n = route_gdf["n"].iloc[-1]
    source = network.nodes[source_n]
    target = network.nodes[target_n]

    structure_types = {"S": "Structure", "L": "Lock", "B": "Bridge"}

    return {
        "total_length_m": total_length_m,
        "n_edges": n_edges,
        "n_nodes": n_nodes,
        "source_n": source_n,
        "target_n": target_n,
        "source_geometry": shapely.geometry.mapping(
            network.nodes[source_n]["geometry"]
        ),
        "target_geometry": shapely.geometry.mapping(
            network.nodes[target_n]["geometry"]
        ),
    }


def get_route(waypoints, network):
    """
    Compute route response based on a list of waypoints.

    Parameters
    ----------
    waypoints : list
        A list of waypoints as node ids.
    network : networkx.Graph
        The network on which to compute the route.

    Returns
    -------
    route : dict
        The route as a dictionary.
    """
    route_gdf = make_route_gdf(waypoints, network)
    metadata = route_metadata(route_gdf, network)
    route = json.loads(route_gdf.to_json())
    route_properties = route.get("properties", {})
    route_properties.update(metadata)
    route["properties"] = route_properties
    return route


@functools.lru_cache(maxsize=100)
def get_edges_gdf(graph):
    """
    Convert graph to edge list of geodataframes, also add bathymetry info. Transform 
    to utm for spatial matching purposes.
    
    Parameters
    ----------
    graph : networkx.Graph
        The graph to convert.
    
    Returns
    -------
    edges_gdf : geopandas.GeoDataFrame
        The edges as a geopandas dataframe with bathymetry info.

    """
    edges_df = nx.to_pandas_edgelist(graph)
    edges_gdf = gpd.GeoDataFrame(edges_df, geometry="geometry", crs=4326)

    src_path = dtv_backend.get_src_path()

    version = "0.3"

    bathy_gdf = gpd.read_file(src_path / "data" / f"edges_{version}_with_bathy.geojson")
    bathy_graph = nx.from_pandas_edgelist(
        bathy_gdf, source="start-id", target="end-id", edge_attr=True
    )

    # lookup corresponding values for each row
    def get_bathy(row):
        edge = bathy_graph.edges[row["source"], row["target"]]
        result = pd.Series(
            {
                "nap_p5": edge["nap_p5"],
                "nap_p50": edge["nap_p50"],
                "nap_p95": edge["nap_p95"],
                "lat_p5": edge["lat_p5"],
                "lat_p50": edge["lat_p50"],
                "lat_p95": edge["lat_p95"],
            }
        )
        return result

    bathy_columns = edges_gdf.apply(get_bathy, axis=1)
    # add bathymetry columns
    edges_gdf = pd.merge(edges_gdf, bathy_columns, left_index=True, right_index=True)
    return edges_gdf


def has_structures(route, graph):
    """
    Are there any structures on this route?
    
    Parameters
    ----------
    route : list
        A list of nodes representing the route.
    graph : networkx.Graph
        The graph on which to check for structures.

    Returns
    -------
    has_structures : bool
        True if there are structures on the route, False otherwise.
    """
    has_structures = False
    for e in pairwise(route):
        edge = graph.edges[e]
        structure = extract_structure(e)
        if structure is not None:
            has_structures = True
            break
    return has_structures


def route_to_sea(source, graph):
    """
    Determine if source node has a route to sea on the graph.

    Parameters
    ----------
    source : str
        The source node id.
    graph : networkx.Graph
        The graph on which to check for a route to sea.

    Returns
    -------
    route_to_sea : bool
        True if there is a route to sea, False otherwise.
    """
    sea_nodes = [
        # rotterdam
        "8866305",
        # roompot
        "8864380",
        # IJmuiden
        "8864991",
        # Den Helder
        "8867031",
        # Eemshaven
        "8863991",
    ]
    route_to_sea = False
    for target in sea_nodes:
        route = nx.shortest_paths.shortest_path(graph, source=source, target=target)
        if not has_structures(route, graph):
            route_to_sea = True
            break
    return route_to_sea


def path_restricted_to_cemt_class(
    graph, origin, destination, ship_cemt_classe, ordered_cemt_classes
):
    """find a path restricted to allowed cemt classes

    Parameters
    ----------
    graph : networkx.Graph
        graph in which to find a path. graph edges should have information 'cemt'.
    origin : str
        origin node id
    destination : str
        destination node id
    ship_cemt_classe : str
        cemt class of the ship.
    """
    # define order of cemt classes

    # create function to compute weights for this ship
    compute_weight = functools.partial(
        __compute_weight,
        ship_cemt_classe=ship_cemt_classe,
        ordered_cemt_classes=ordered_cemt_classes,
    )

    # find the path
    path = nx.dijkstra_path(graph, origin, destination, weight=compute_weight)
    return path


def path_restricted_to_rws_class(
    graph, origin, destination, ship_rws_classe, ordered_cemt_classes
):
    """find a path restricted to allowed cemt classes

    Parameters
    ----------
    graph : networkx.Graph
        graph in which to find a path. graph edges should have information 'cemt'.
    origin : str
        origin node id
    destination : str
        destination node id
    ship_cemt_classe : str
        cemt class of the ship.
    """
    ship_cemt_classe = __scheepstype_rws_to_cemt(ship_rws_classe)
    return path_restricted_to_cemt_class(
        graph,
        origin,
        destination,
        ship_cemt_classe=ship_cemt_classe,
        ordered_cemt_classes=ordered_cemt_classes,
    )


def __compute_weight(
    origin, target, dictionary_edge, ship_cemt_classe, ordered_cemt_classes
):
    # order classes from smallest to largest

    if (
        not dictionary_edge["Code"] in ordered_cemt_classes
        or not ship_cemt_classe in ordered_cemt_classes
    ):
        return dictionary_edge["length_m"]
    elif (
        ordered_cemt_classes[dictionary_edge["Code"]]
        < ordered_cemt_classes[ship_cemt_classe]
    ):
        return np.nan
    else:
        return dictionary_edge["length_m"]


def __scheepstype_rws_to_cemt(rws_classe):
    rws_to_cemt = {
        "M0": "0",
        "M1": "I",
        "M2": "II",
        "M3": "III",
        "M4": "III",
        "M5": "III",
        "M6": "IVa",
        "M7": "IVa",
        "M8": "Va",
        "M9": "Va",
        "M10": "VIa",
        "M11": "VIa",
        "M12": "VIa",
    }
    return rws_to_cemt[rws_classe]


# klasse to shiplength. Gebruikt ondergrenzen uit richtlijn vaarwegen 2020, tabel 8.
rws_klasse_to_shiplength = {
    "M0": 20,
    "M1": 38.5,
    "M2": 50,
    "M3": 55,
    "M4": 67,
    "M5": 80,
    "M6": 80,
    "M7": 105,
    "M8": 110,
    "M9": 135,
    "M10": 110,
    "M11": 135,
    "M12": 135,
    "C1b": 38.5,
    "C1L": 77,
    "C2L": 170,
    "C3L": 170,
    "C2b": 85,
    "C3b": 95,
    "C4": 185,
    "BO1": 55,
    "BO2": 60,
    "BO3": 80,
    "BO4": 85,
    "BI": 85,
    "BII-1": 95,
    "BIIa-1": 92,
    "BIIL-1": 125,
    "BII-2L": 170,
    "BII-2b": 95,
    "BII-4": 185,
    "BII-6b": 270,
    "BII-6L": 195,
}

rws_klasse_to_shipwidth = {
    "M0": 5,
    "M1": 5.05,
    "M2": 6.6,
    "M3": 7.2,
    "M4": 8.2,
    "M5": 8.2,
    "M6": 9.5,
    "M7": 9.5,
    "M8": 11.4,
    "M9": 11.4,
    "M10": 13.5,
    "M11": 14.2,
    "M12": 17.0,
    "C1b": 10.1,
    "C1L": 5.05,
    "C2L": 9.5,
    "C3L": 11.4,
    "C2b": 19,
    "C3b": 22.8,
    "C4": 22.8,
    "BO1": 5.2,
    "BO2": 6.6,
    "BO3": 7.5,
    "BO4": 8.2,
    "BI": 9.5,
    "BII-1": 11.4,
    "BIIa-1": 11.4,
    "BIIL-1": 11.4,
    "BII-2L": 11.4,
    "BII-2b": 22.8,
    "BII-4": 22.8,
    "BII-6b": 22.8,
    "BII-6L": 34.2,
}
