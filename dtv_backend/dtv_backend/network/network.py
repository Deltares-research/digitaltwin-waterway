import logging
import functools
import io
import tempfile
import urllib

import shapely.wkt
import shapely.geometry
import numpy as np
import networkx as nx
import requests
import pyproj

from diskcache import Cache

cache = Cache(directory='./cache')



logger = logging.getLogger(__name__)

# define the coorinate system
geod = pyproj.Geod(ellps="WGS84")


# The network version 0.1 contains the lat/lon distance in a length property.
# But we need the "great circle" or projected distance.
# Let's define a function to recompute it.
def edge_length(edge):
    """compute the great circle length of an edge"""
    # get the geometry
    geom = edge['geometry']
    # get lon, lat
    lats, lons = np.array(geom).T
    distance = geod.line_length(lons, lats)
    return distance

# now create the function can load the network

# store the result so it will immediately give a result
@cache.memoize(expire=3600 * 24)
def load_fis_network(url):
    """load the topological fairway information system network"""

    logger.info(f'storing results in {cache.directory}')

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
    G = nx.read_yaml(f.name)

    # the temp file can be deleted
    del f


    # some brief info
    n_bytes = len(resp.content)
    msg = '''Loaded network from {url} file size {mb:.2f}MB. Network has {n_nodes} nodes and {n_edges} edges.'''
    summary = msg.format(url=url, mb=n_bytes / 1000**2, n_edges=len(G.edges), n_nodes=len(G.nodes))
    logger.info(summary)


    # The topological network contains information about the original geometry.
    # Let's convert those into python shapely objects for easier use later
    for n in G.nodes:
        G.nodes[n]['geometry'] = shapely.geometry.Point(G.nodes[n]['X'], G.nodes[n]['Y'])
    for e in G.edges:
        edge = G.edges[e]
        edge['geometry'] = shapely.wkt.loads(edge['Wkt'])
        edge['length'] = edge_length(edge)

    return G


# Creating a library of some interesting locations
def find_closest_node(G, point):
    """ Find the node on graph G that is closest to the given
    shapely.geometry.Point point """
    distance = np.full((len(G.nodes)), fill_value=np.nan)
    for ii, n in enumerate(G.nodes):
        distance[ii] = point.distance(G.nodes[n]['geometry'])
    name_node = list(G.nodes)[np.argmin(distance)]
    distance_node = np.min(distance)
    return name_node, distance_node
