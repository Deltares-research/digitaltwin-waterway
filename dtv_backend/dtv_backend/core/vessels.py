# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 20:22:05 2020

@author: KLEF
"""
#%% Import modules
import uuid

# our software
import opentnsim.core as TNcore
import openclsim.core as CLcore


#%% Define a general TransportProcessingResource
import dtv_backend.core.move_module as BackendVesselMovement

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


#%% Function to provide a general site
def provideVessel(env,
                    geometry,
                    name = 'standard M8 vessel',
                    id = str(uuid.uuid1()),
                    loading_rate = 1,
                    unloading_rate = 1,
                    capacity = 3000,
                    compute_v = default_compute_v_provider(),
                    route = None,
                    vessel_type = 'M8',
                    installed_power = 1000,
                    width = 10, 
                    length = 110, 
                    height_empty = 8, 
                    height_full = 4, 
                    draught_empty = 2, 
                    draught_full = 6):
    """
    Provides a standardized transport processing resource
    """
    # define the vessel data
    vessel_data = {
            "env": env,
            "name": name,
            "id": id,
            "geometry": geometry,
            "loading_rate": loading_rate,
            "unloading_rate": unloading_rate,
            "capacity": capacity,
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

    

