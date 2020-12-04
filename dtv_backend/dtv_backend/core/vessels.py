# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 20:22:05 2020

@author: KLEF
"""
#%% Import modules
import uuid
import logging

import geojson
import shapely.geometry

# our software
import opentnsim.core as TNcore
import openclsim.core as CLcore


#%% Define a general TransportProcessingResource
import dtv_backend.core.move_module as BackendVesselMovement
from dtv_backend.network.network_utilities import find_closest_node


logger = logging.getLogger(__name__)

TransportProcessingResource = type(
    "TransportProcessingResource",
    (
        CLcore.Identifiable,
        BackendVesselMovement.ContainerDependentMovable,
        TNcore.VesselProperties,
        TNcore.Routeable,
        CLcore.HasResource,
        CLcore.Processor,
        CLcore.LoadingFunction,
        CLcore.UnloadingFunction,
        TNcore.ExtraMetadata
    ),
    {},
)


#%%
def default_compute_v_provider(v_empty=5, v_full=4.5):
    return lambda x: 10


def feature2vessel(feature, env):
    """convert feature to vessel object"""
    feature = geojson.Feature(**feature)
    vessel_data = {}
    vessel_data.update(feature['properties'])

    # copy items that we know
    mapping = {
        'RWS-class': 'vessel_type',
        'Beam [m]': 'width',
        'Length [m]': 'length',
        'Draught loaded [m]': 'draught_full',
        'Draught empty [m]': 'draught_empty'
    }
    for old, new in mapping.items():
        if old in vessel_data and new not in vessel_data:
            vessel_data[new] = vessel_data[old]

    # fill in missing items
    if 'Height average [m]' in vessel_data and 'height_full' not in vessel_data:
        height_average = vessel_data['Height average [m]']
        draught_average = vessel_data['Draught average [m]']
        draught_empty = vessel_data['Draught empty [m]']
        draught_full = vessel_data['Draught loaded [m]']
        height_empty = height_average - (draught_average - draught_empty)
        height_full = height_average - (draught_average - draught_full)
        logger.info(
            'Defining draught function: height empty %s, full %s',
            height_empty,
            height_full
        )
        vessel_data['height_empty'] = height_empty
        vessel_data['height_full'] = height_full


    # defaults
    vessel_data['installed_power'] = 1000
    vessel_data['compute_v'] = default_compute_v_provider()
    # this is determined by activity
    vessel_data['route'] = None

    # other
    vessel_data['env'] = env

    point = shapely.geometry.asShape(
        geojson.Feature(**feature).geometry
    )
    closest_node, distance = find_closest_node(env.FG, point)

    vessel_data['node'] = closest_node
    vessel_data['distance_to_node'] = distance

    geometry = env.FG.nodes[closest_node]['geometry']
    vessel_data['geometry'] = geometry

    vessel = TransportProcessingResource(**vessel_data)
    return vessel


#%% Function to provide a general site
def provideVessel(
        env,
        geometry,
        name = 'standard M8 vessel',
        id = str(uuid.uuid1()),
        loading_rate = 1,
        unloading_rate = 1,
        capacity = 3000,
        allowable_draught = None,
        compute_v = default_compute_v_provider(),
        route = None,
        vessel_type = 'M8',
        installed_power = 1000,
        width = 10,
        length = 110,
        height_empty = 8,
        height_full = 4,
        draught_empty = 2,
        draught_full = 6
):
    """
    Provides a standardized transport processing resource

    ENTER RATES ((UN)LOADING, SPEED) AS UNITS/HOUR (e.g. km/h)
    (simpy requires units/seconds which is corrected for to get 'real' times)

    """
    # define the vessel data
    vessel_data = {
            "env": env,
            "name": name,
            "id": id,
            "geometry": geometry,
            "loading_rate": loading_rate/3600,
            "unloading_rate": unloading_rate/3600,
            "capacity": capacity,
            "allowable_draught": allowable_draught,
            "compute_v": compute_v,
            "route": route,
            'vessel_type': vessel_type,
            'installed_power': installed_power,
            'width': width,
            'length': length,
            'height_empty': height_empty,
            'height_full': height_full,
            'draught_empty': draught_empty,
            'draught_full': draught_full
        }

    return TransportProcessingResource(**vessel_data)


#%%
