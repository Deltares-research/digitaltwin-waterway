# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 20:22:05 2020

@author: KLEF
"""
#%% Import modules
import uuid
import numpy as np
import shapely.geometry
import geojson

# our software
import openclsim.core as CLcore
import opentnsim.core as TNcore

from dtv_backend.network.network_utilities import find_closest_node


#%% Define a general site
Site = type(
    "Site",
    (
        CLcore.Identifiable,
        CLcore.Log,
        CLcore.Locatable,
        CLcore.HasContainer,
        CLcore.HasResource,
        CLcore.Processor,
        CLcore.LoadingFunction,
        CLcore.UnloadingFunction,
        TNcore.ExtraMetadata
    ),
    {},
)

def feature2site(feature, env):
    """convert an input site feature (geojson) to a Site object"""

    data_site = {}
    data_site.update(feature['properties'])
    data_site['env'] = env
    data_site['ID'] = str(uuid.uuid1())
    # snap to the network, convert to shapely point
    point = shapely.geometry.asShape(
        geojson.Feature(**feature).geometry
    )
    closest_node, distance = find_closest_node(env.FG, point)
    data_site['node'] = closest_node
    data_site['distance_to_node'] = distance
    # lookup corresponding geometry
    geometry = env.FG.nodes[closest_node]['geometry']
    data_site['geometry'] = geometry
    site = Site(**data_site)
    return site





#%% Function to provide a general site
def provideSite(env, point, name, capacity, level, loading_rate=1, unloading_rate=1):
    """
    Returns a Site that can be used in simulation based on a given shapely.geometry.Point

    ENTER THE (UN)LOADING RATES AS UNITS/HOUR

    Parameters
    ----------
    env : TYPE
        DESCRIPTION.
    point : TYPE
        DESCRIPTION.
    name : TYPE
        DESCRIPTION.
    capacity : TYPE, optional
        DESCRIPTION. The default is np.inf.
    level : TYPE, optional
        DESCRIPTION. The default is 1000.
    loading_rate : TYPE, optional
        DESCRIPTION. The default is 1.
    unloading_rate : TYPE, optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    # find the closest node to the desired point
    closest_node = find_closest_node(env.FG, point)[0]

    # define the data for the site
    data_site = {
        "env": env,
        "name": name,
        "ID": str(uuid.uuid1()),
        "geometry": env.FG.nodes[closest_node]['geometry'],
        "capacity": capacity,
        "level": level,
        "loading_rate": loading_rate/3600,
        "unloading_rate": unloading_rate/3600,
    }

    # define the site object
    return Site(**data_site)
