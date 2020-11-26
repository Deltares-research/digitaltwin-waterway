# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 15:07:26 2020

@author: KLEF
"""
# define fleet class 
# fleet class is used to store all fleet related information
# move activities should be able to work with the fleet
# fleet consists of vessels

from dtv_backend.core import vessels as backendVessels
from dtv_backend.fleet import NPRCfleet
from dtv_backend.fleet import Dancerfleet


#%%
def loadDTVFleet(env):
    # load NPRC fleet
    #bulk_fleet = NPRCfleet.provideNPRCfleet(env)
    # load Dancer fleet
    #container_fleet = Dancerfleet.provideDancerfleet(env)
    
    # to be separately returned
    # container fleet
    # bulk fleet
    return

#%%
def provideFleet(end, vessel_dict):
    # is supposed to return a list of vessels making up the fleet
    # vessel_dict says {'vessel name':'amount'}
    # create each vessel from the database
    fleet = []
    return fleet