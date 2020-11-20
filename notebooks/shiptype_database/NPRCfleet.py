# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 14:45:08 2020

@author: KLEF
"""

import os
import uuid 
import pandas as pd

import openclsim.core as core
from vesselProperties import createVesselProperties

#%% Define required info from databases
required_fleet_info = ['Ship Name', 
                       'Beam [m]', 
                       'Length [m]', 
                       'Load capacity [ton]', 
                       'Expected ship-class']
    
required_shiptypes_info = {
                    'cemt_class': 'CEMT-class',
                    'description_dutch': 'Description (Dutch)',
                    'description_english': 'Description (English)',
                    'draught_empty': 'Draught empty [m]',
                    'draught_full': 'Draught loaded [m]',
                    'vessel_type': 'Vessel type'
                    }

#%% Create the generic class for an object that can move and transport 
TransportResource = type(
    "TransportResource",
    (
        core.Identifiable,  # Give it a name
        core.Log,  # Allow logging of all discrete events
        core.ContainerDependentMovable,  # A moving container, so capacity and location
    ),
    {},
)

# for now let the speed be 10km/h (stroomopwaarts)
def compute_v_provider(v_empty, v_full):
    return lambda x: 10


#%% Generate the NPRC fleet
def provideNPRCfleet(env):
:       # TODO: input dict with {<vessel_name>:<number>}
    """
    Function that generates the NPRC fleet as dictionary from a database and 
    adds it to the desired simpy environment
    """
    NPRCfleet = {}
    fleet_database = loadFleetDatabase()
    shiptype_database = loadShiptypeDatabase()
    
    for ix, vessel_info in fleet_database.iterrows():
        vessel_name = vessel_info['Ship Name']
        rws_class = vessel_info['Expected ship-class']
        
        # initiate with default info required by the TransportResource type
        data_vessel = {
                "env": env,
                "ID": str(uuid.uuid1()),
                "name": vessel_name,
                "compute_v": compute_v_provider(5, 4.5),
                "geometry": None,
                "capacity": vessel_info['Load capacity [ton]'],
        }
        
        vessel = TransportResource(**data_vessel) 
        
        # add additional vessel properties from both databases
        vessel_properties = {
                "rws_class": rws_class, 
                "width": vessel_info['Beam [m]'],
                "length": vessel_info['Length [m]'],
        }
        
        shiptype_info = shiptype_database.loc[shiptype_database['RWS-class']==rws_class][required_shiptypes_info.values()].to_dict('records')
        if len(shiptype_info) == 1:
            shiptype_info = shiptype_info[0]
            # add the required property fields to the 
            for key, value in required_shiptypes_info.items():
                vessel_properties.update({key:shiptype_info[value]})
        else:
            continue
        
        properties = createVesselProperties(**vessel_properties)
        vessel.properties = properties
        
        # generate the vessel with the 
        NPRCfleet[vessel_name] = vessel
    
    return NPRCfleet


#%% import the NPRC fleet information
def loadFleetDatabase():
    assert os.path.isfile('fleet_NPRC.xlsx'), "'fleet_NPRC.xlsx' fleet database not found!"
    fleet_database = pd.read_excel('fleet_NPRC.xlsx')
    
    contains_all, missing = containsRequiredColumns(fleet_database, required_fleet_info)
    assert contains_all, f"'fleet_NPRC.xlsx' misses the following columns: {missing}"
    
    return fleet_database

#%% import the general shiptype database containing the CEMT info
def loadShiptypeDatabase(): 
    assert os.path.isfile('DTV_shiptypes_database.xlsx'), "'DTV_shiptypes_database.xlsx' fleet database not found!"
    shiptype_database = pd.read_excel('DTV_shiptypes_database.xlsx')
    
    contains_all, missing = containsRequiredColumns(shiptype_database, required_shiptypes_info.values())
    assert contains_all, f"'DTV_shiptypes_database.xlsx' misses the following columns: {missing}"
    
    return shiptype_database
    
#%% aux function to check whether dataframe contains required columns
def containsRequiredColumns(df, required_cols):
    missing = []
    contains_cols = [col in df.columns for col in required_cols]
    contains_all = all(contains_cols)
    
    if not contains_all:
        missing = [x for x, y in zip(required_cols, contains_cols) if y == False]
        
    return contains_all, missing

