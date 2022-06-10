# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 08:43:06 2020

@author: KLEF
"""

#%%
import datetime
import simpy

from NPRCfleet import provideNPRCfleet

#%%
simulation_start = datetime.datetime(2020, 10, 27).timestamp()
my_env = simpy.Environment(initial_time=simulation_start)

#%%
# NPRC_fleet = provideNPRCfleet(my_env)
