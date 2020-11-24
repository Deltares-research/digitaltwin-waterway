# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 15:06:43 2020

@author: KLEF
"""

# import openCLSim activity class
from openclsim.model.base_activities import GenericActivity

# import the required functionalities from openTNSim
import openclsim.core as core

# import graph modules
import dtv_backend.network.network_utilities as GraphUtils


#%%
class MoveActivity(GenericActivity):
    """
    MoveActivity Class forms a specific class for a single move activity within a simulation.

    It deals with a single origin container, destination container and a single combination of equipment
    to move substances from the origin to the destination. It will initiate and suspend processes
    according to a number of specified conditions. To run an activity after it has been initialized call env.run()
    on the Simpy environment with which it was initialized.

    To check when a transportation of substances can take place, the Activity class uses three different condition
    arguments: start_condition, stop_condition and condition. These condition arguments should all be given a condition
    object which has a satisfied method returning a boolean value. True if the condition is satisfied, False otherwise.

    destination: object inheriting from HasContainer, HasResource, Locatable, Identifiable and Log
    mover: moves to 'origin' if it is not already there, is loaded, then moves to 'destination' and is unloaded
           should inherit from Movable, HasContainer, HasResource, Identifiable and Log
           after the simulation is complete, its log will contain entries for each time it started moving,
           stopped moving, started loading / unloading and stopped loading / unloading
    start_event: the activity will start as soon as this event is triggered
                 by default will be to start immediately
    """

    def __init__(self, mover, destination, show=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.destination = destination
        self.mover = mover
        self.print = show
        if not self.postpone_start:
            self.start()

    def start(self):
        self.register_process(main_proc=self.move_process, show=self.print)
        
    # TODO: replace the move provess below by openTNSim functionalies
    def move_process(self, activity_log, env):
        """
        Return a generator which can be added as a process to a simpy.Environment.

        In the process, a move will be made
        by the mover, moving it to the destination.

        activity_log: the core.Log object in which log_entries about the activities progress will be added.
        env: the simpy.Environment in which the process will be run
        mover: moves from its current position to the destination
            should inherit from WHICH TNSIM FUNCTIONALITIES APPLY HERE?
        destination: the location the mover will move to
                    should inherit from core.Locatable
        engine_order: optional parameter specifying at what percentage of the maximum speed the mover should sail.
                    for example, engine_order=0.5 corresponds to sailing at 50% of max speed
        """
        message = "move activity {} of {} to {}".format(
            self.name, self.mover.name, self.destination.name
        )
        yield from self._request_resource(self.requested_resources, self.mover.resource)

        start_time = env.now
        args_data = {
            "env": env,
            "activity_log": activity_log,
            "message": message,
            "activity": self,
        }
        yield from self.pre_process(args_data)

        activity_log.log_entry(
            message,
            env.now,
            -1,
            self.mover.geometry,
            activity_log.id,
            core.LogState.START,
        )

        start_mover = env.now
        self.mover.ActivityID = activity_log.id
        
        # I think here we need to use the functionalities from openTNSim
        # Make sure that we select a path between two nodes
        origin_node = GraphUtils.find_closest_node(env.network, self.mover.geometry)
        destination_node = GraphUtils.find_closest_node(env.network, self.destination.geometry)
        
        # Then set the route from origin to destination node
        self.mover.route = self.mover.get_route(origin=origin_node, 
                                      destination=destination_node, 
                                      graph=env.FG, 
                                      minWidth=self.mover.width, 
                                      minHeight=self.mover.current_height, 
                                      minDepth=self.mover.current_draught)
        
        yield from self.mover.move()
        
        # yield from self.mover.move(
        #     destination=self.destination,
        #     engine_order=1,
        #     duration=self.duration,
        #     activity_name=self.name,
        # )

        args_data["start_preprocessing"] = start_time
        args_data["start_activity"] = start_mover
        yield from self.post_process(**args_data)

        self._release_resource(
            self.requested_resources, self.mover.resource, self.keep_resources
        )

        # work around for the event evaluation
        # this delay of 0 time units ensures that the simpy environment gets a chance to evaluate events
        # which will result in triggered but not processed events to be taken care of before further progressing
        # maybe there is a better way of doing it, but his option works for now.
        yield env.timeout(0)

        activity_log.log_entry(
            message,
            env.now,
            -1,
            self.mover.geometry,
            activity_log.id,
            core.LogState.STOP,
        )