"""Routines for postprocessing the results of OpenCLSim/OpenTNSim"""

import geopandas as gpd
import shapely.wkt


def path2gdf(path, network):
    """export a path to a geodataframe"""
    edges = []
    for a, b in zip(path[:-1], path[1:]):
        edge = network.edges[a, b]
        # TODO: add geometry to edges
        geometry = shapely.wkt.loads(edge['Wkt'])
        edge['geometry'] = geometry
        edges.append(edge)
    gdf = gpd.GeoDataFrame(edges)
    return gdf
