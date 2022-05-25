# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 17:10:36 2020

@author: KLEF
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

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pyproj
import requests
import scipy.interpolate
import shapely
import shapely.geometry
import shapely.wkt
from diskcache import Cache

# add pairwise to itertools for python < 3.10
if not hasattr(itertools, "pairwise"):

    def pairwise(iterable):
        # pairwise('ABCDEFG') --> AB BC CD DE EF FG
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    itertools.pairwise = pairwise


try:
    cache = Cache(directory="./cache")
except:
    cache = {}


logger = logging.getLogger(__name__)

package_path = pathlib.Path(__file__).parent.parent

# define the coorinate system
geod = pyproj.Geod(ellps="WGS84")


def memoize(*args, **kwargs):
    """decorate with caching"""
    try:
        f = cache.memoize(*args, **kwargs)
    except AttributeError:
        f = functools.lru_cache
    return f


# The network version 0.1 contains the lat/lon distance in a length property.
# But we need the "great circle" or projected distance.
# Let's define a function to recompute it.
def edge_length(edge):
    """compute the great circle length of an edge"""
    # get the geometry
    geom = edge["geometry"]
    # get lon, lat
    lats, lons = np.array(geom).T
    distance = geod.line_length(lons, lats)
    return distance


# now create the function can load the network

# store the result so it will immediately give a result
@memoize(expire=3600 * 24)
def load_fis_network(url):
    """load the topological fairway information system network"""

    logger.info(f"storing results in {cache}")

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
    G = nx.read_gpickle(f.name)

    # the temp file can be deleted
    del f

    # some brief info
    n_bytes = len(resp.content)
    msg = """Loaded network from {url} file size {mb:.2f}MB. Network has {n_nodes} nodes and {n_edges} edges."""
    summary = msg.format(
        url=url, mb=n_bytes / 1000 ** 2, n_edges=len(G.edges), n_nodes=len(G.nodes)
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
    name_node : TYPE
        DESCRIPTION.
    distance_node : TYPE
        DESCRIPTION.

    """
    distance = np.full((len(G.nodes)), fill_value=np.nan)
    for ii, n in enumerate(G.nodes):
        distance[ii] = point.distance(G.nodes[n]["geometry"])
    name_node = list(G.nodes)[np.argmin(distance)]
    distance_node = np.min(distance)
    return name_node, distance_node


def find_closest_edge(G, point):
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
    compute the max draught on the route. If none of the locations where we know the discharge depth relation is on the route, return the default max_draught.
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

    return 6


def determine_max_layers(height):
    """determine max number of container layers as a function of available height on the route"""

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
    """create a new constrained graph, based on dimensions, of the same type as graph and find the shortest path"""
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
    """compute shortest path on a graph"""
    path = nx.dijkstra_path(graph, source, destination, weight=weight)
    return path


def compute_path_length(graph, path, key="length_m"):
    """aux fcn to compute distance of a path"""
    total_distance = 0
    for e in zip(path[:-1], path[1:]):
        edge_distance = graph.edges[e][key]
        total_distance += edge_distance
    return total_distance


def extract_structure(e):
    structure_re = re.compile("^(?P<structure_code>[SLB])(?P<structure_id>\d+)_[AB]$")

    structure_types = {"S": "Structure", "L": "Lock", "B": "Bridge"}
    source_match = structure_re.match(e[0])
    target_match = structure_re.match(e[0])
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
    """compute a route and return a geopandas dataframe with the route"""
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
    """compute metadata for the route"""
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
    """compute route response based on a list of waypoints"""
    route_gdf = make_route_gdf(waypoints, network)
    metadata = route_metadata(route_gdf, network)
    route = json.loads(route_gdf.to_json())
    route_properties = route.get("properties", {})
    route_properties.update(metadata)
    route["properties"] = route_properties
    return route
