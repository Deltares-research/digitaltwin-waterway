"""This module contains simple components for the Digital Twin Fairways backend."""
import uuid
import datetime
import itertools
import logging

import numpy as np
import simpy
import shapely.geometry

# timeboard registration
from pint import UnitRegistry

import dtv_backend.fis
import dtv_backend.logbook
import dtv_backend.scheduling
import dtv_backend.berthing

ureg = UnitRegistry()


class Operator(dtv_backend.logbook.HasLog):
    """This class represents a fleet operator."""

    def __init__(self, ships=None, n_margin=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not ships:
            raise ValueError("Non empty list of ships is required")

        self.fleet = simpy.Store(self.env, capacity=len(ships))
        # create list of tasks, any ship can pick them up
        self.tasks = simpy.Store(self.env, capacity=len(ships))
        for ship in ships:
            self.fleet.put(ship)
        # number of extra tasks to send as a safety margin
        # TODO: implement ship -> operator communication for replanning
        self.n_margin = n_margin

    def send_task(self, task):
        """return send task request"""
        return self.tasks.put(task)

    def get_task(self):
        """return get task request"""
        return self.tasks.get()

    def plan(self, source, destination):
        """A process which prepares tasks."""
        with self.log_context(message="Plan", description=f"Plan ({self.name})"):
            total_work = source.container.level
            # estimate max_load per task
            # TODO: implement smarter planning
            #
            max_load = min(
                max(ship.max_load for ship in self.fleet.items),
                source.max_load,
            )
            min_load = min(ship.max_load for ship in self.fleet.items)
            # estimate n tasks + 1 reserve
            n_tasks = int(np.ceil(total_work / min_load))
            # safety margin
            n_tasks += self.n_margin
            for i in range(n_tasks):
                if source.container.level <= 0:
                    # source port is empty, we're  done
                    break
                # Send out tasks
                with self.log_context(
                    message="Task",
                    description=f"Sending task ({self.name})",
                    max_load=max_load,
                    source=source,
                    destination=destination,
                ):
                    # Time it takes to send an assignment (1 hour)
                    yield self.env.timeout(3600)
                    self.send_task(
                        {
                            "source": source,
                            "destination": destination,
                            "max_load": max_load,
                        }
                    )


class Port(dtv_backend.logbook.HasLog):
    """
    A port has a limited number of cranes (num_cranes) and a cargo storage with a
    capacity (capacity) and a initial level (level) to load or unload ships in parallel.

    Ships have to request one of the cranes. When they got one, they
    can load or unload an amount of cargo and wait for it to moved (which
    takes loading rate * min(ship.max_load, available) minutes).

    The port has a geometry, which can be used for navigation purposes.
    """

    def __init__(
        self,
        env,
        name="Port",
        num_cranes=1,
        loading_rate=1,
        level=0,
        capacity=1,
        geometry=None,
        **kwargs,
    ):
        super().__init__(env=env)
        self.name = name
        self.crane = simpy.Resource(env, num_cranes)
        self.loading_rate = loading_rate
        self.container = simpy.Container(env, init=level, capacity=capacity)
        self.geometry = shapely.geometry.shape(geometry)
        self.metadata = kwargs

    @property
    def node(self):
        """return the closest FIS node to the port geometry"""
        node, dist = dtv_backend.fis.find_closest_node(self.env.FG, self.geometry)
        return node

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        return self.container.capacity - self.container.level

    def load(self, source, destination, max_load=None):
        """
        The loading processes. It takes a ``ship`` and loads it with maximal
        (max_load).
        """
        available = source.container.level
        # check how much load we can maximally transfer based on the  we are 
        # requested to load max_load, but
        if max_load is not None:
            max_load = min(max_load, destination.max_load)
        else:
            max_load = destination.max_load
        cargo_to_move = min(available, max_load)
        if not cargo_to_move:
            # this yields and stops the iteratur
            return self.env.timeout(0)

        # tonne / (tonne / hour) -> s
        load_time = (
            cargo_to_move
            * ureg.metric_ton
            / (self.loading_rate * (ureg.metric_ton / ureg.hour))
        )
        load_time = load_time.to(ureg.second).magnitude

        # log cargo levels before/after
        with self.log_context(
            message="Load",
            description=f"Loading ({source.name}) -> ({destination.name})",
            destination=destination.container,
            source=source.container,
            geometry=self.geometry,
            value=cargo_to_move,
        ):
            source.container.get(cargo_to_move)
            # move it to the destination
            destination.container.put(cargo_to_move)
            # how long did this take
            yield self.env.timeout(load_time)
