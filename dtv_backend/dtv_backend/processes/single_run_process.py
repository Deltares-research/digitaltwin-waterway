# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 15:11:58 2020

@author: KLEF
"""
# openclsim.model.move_activity import MoveActivity
from openclsim.model.sequential_activity import SequentialActivity
from openclsim.model.shift_amount_activity import ShiftAmountActivity
from openclsim.model.while_activity import WhileActivity

# import the graph interaction from opentnsim_based_functionalities
from dtv_backend.activities.move_activity import MoveActivity

#%% Functionality to create a single run process but with the moving functionalities of openTNsim
# note that this is in basis a copy from openCLSim

# copy from the openCLSim, in which we should define the move activity using openTNSim
# move from origin to destination --> determine path
# move from destination to origin --> determine path 
def single_run_process(
    env,
    registry,
    name,
    origin,
    destination,
    mover,
    loader,
    unloader,
    start_event=None,
    stop_event=[],
    requested_resources={},
    postpone_start=False,
):
    """Single run activity for the simulation."""
    if stop_event == []:
        stop_event = [
            {
                "or": [
                    {"type": "container", "concept": origin, "state": "empty"},
                    {"type": "container", "concept": destination, "state": "full"},
                ]
            }
        ]

    single_run = [
        MoveActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            postpone_start=True,
            name=f"{name} sailing empty",
            mover=mover,
            destination=origin,
        ),
        ShiftAmountActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            postpone_start=True,
            phase="loading",
            name=f"{name} loading",
            processor=loader,
            origin=origin,
            destination=mover,
        ),
        MoveActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            postpone_start=True,
            name=f"{name} sailing filled",
            mover=mover,
            destination=destination,
        ),
        ShiftAmountActivity(
            env=env,
            registry=registry,
            requested_resources=requested_resources,
            phase="unloading",
            name=f"{name} unloading",
            postpone_start=True,
            processor=unloader,
            origin=mover,
            destination=destination,
        ),
    ]

    activity = SequentialActivity(
        env=env,
        name=f"{name} sequence",
        registry=registry,
        sub_processes=single_run,
        postpone_start=True,
    )

    while_activity = WhileActivity(
        env=env,
        name=name,
        registry=registry,
        sub_process=activity,
        condition_event=stop_event,
        start_event=start_event,
        postpone_start=postpone_start,
    )

    return single_run, activity, while_activity