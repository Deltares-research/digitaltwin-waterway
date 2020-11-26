# -*- coding: utf-8 -*-
"""
Created on Thu Nov 26 10:48:03 2020

@author: KLEF
"""
from dtv_backend.processes.single_run_process import single_run_process

def single_run_process_fleet(fleet, env, origin, destination, loader, unloader):
    single_runs = []
    activities = []
    while_activities = []
    
    for mover in fleet:
        single_run, activity, while_activity  = single_run_process(
                                                                    name=f"{mover.name} transport process single run",
                                                                    registry={},
                                                                    env=env,
                                                                    origin=origin,
                                                                    destination=destination,
                                                                    mover=mover,
                                                                    loader=loader,
                                                                    unloader=unloader
                                                                )
        single_runs.append(single_run)
        activities.append(activity)
        while_activities.append(while_activity)
    
    return single_runs, activities, while_activities