import uuid
import datetime
import itertools
import logging

import numpy as np
import simpy
import shapely.geometry
from pint import UnitRegistry

import dtv_backend.fis
import dtv_backend.logbook

ureg = UnitRegistry()



class Operator(dtv_backend.logbook.HasLog):
    """This class represents a fleet operator."""
    def __init__(self, env, name='Operator', ships=None, n_margin=0):
        super().__init__(env=env)
        self.name = name
        if not ships:
            raise ValueError("Non empty list of ships is required")

        self.fleet = simpy.Store(env, capacity=len(ships))
        # create list of tasks, any ship can pick them up
        self.tasks = simpy.Store(env, capacity=len(ships))
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
        with self.log(
                message="Plan",
                description=f'Plan ({self.name})'
        ):
            total_work = source.cargo.level
            # estimate max_load per task
            # TODO: implement smarter planning
            max_load = min(
                max(ship.max_load for ship in self.fleet.items),
                source.cargo.level
            )
            min_load = min(ship.max_load for ship in self.fleet.items)
            # estimate n tasks + 1 reserve
            n_tasks = int(np.ceil(total_work / min_load))
            # safety margin
            n_tasks += self.n_margin
            for i in range(n_tasks):
                if source.cargo.level <= 0:
                    # source port is empty, we're  done
                    break
                # Send out tasks
                with self.log(
                        message="Task",
                        description=f"Sending task ({self.name})", max_load=max_load
                ):
                    # Time it takes to send an assignment (1 hour)
                    yield self.env.timeout(3600)
                    self.send_task({
                        "source": source,
                        "destination": destination,
                        "max_load": max_load
                    })


class Port(dtv_backend.logbook.HasLog):
    """
    A port has a limited number of cranes (num_cranes) and a cargo storage with a capacity (capacity) and a initial level (level) to
    load or unload ships in parallel.

    Ships have to request one of the cranes. When they got one, they
    can load or unload an amount of cargo and wait for it to moved (which
    takes loading rate * min(ship.max_load, available) minutes).

    The port has a geometry, which can be used for navigation purposes.
    """
    def __init__(self, env, name='Port', num_cranes=1, loading_rate=1, level=0, capacity=1, geometry=None, **kwargs):
        super().__init__(env=env)
        self.name = name
        self.crane = simpy.Resource(env, num_cranes)
        self.loading_rate = loading_rate
        self.cargo = simpy.Container(env, init=level, capacity=capacity)
        self.geometry = shapely.geometry.shape(geometry)
        self.metadata = kwargs

    @property
    def node(self):
        node, dist = dtv_backend.fis.find_closest_node(self.env.FG, self.geometry)
        return node

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        return self.cargo.capacity - self.cargo.level

    def load(self, source, destination, max_load=None):
        """The loading processes. It takes a ``ship`` and loads it with maximal (max_load)."""
        available = source.cargo.level
        # check how much load we can maximally transfer based on the  we are requested to load max_load, but
        if max_load is not None:
            max_load = min(max_load, destination.max_load)
        else:
            max_load = destination.max_load
        cargo_to_move = min(available, max_load)
        if not cargo_to_move:
            # this yields and stops the iteratur
            return self.env.timeout(0)

        # tonne / (tonne / hour) -> s
        load_time = cargo_to_move * ureg.metric_ton / (self.loading_rate * (ureg.metric_ton / ureg.hour))
        load_time = load_time.to(ureg.second).magnitude


        # log cargo levels before/after
        with self.log(
                message="Load",
                description=f"Loading ({source.name}) -> ({destination.name})",
                destination=destination.cargo,
                source=source.cargo,
                geometry=self.geometry,
                value=cargo_to_move
        ):
            source.cargo.get(cargo_to_move)
            # move it to the destination
            destination.cargo.put(cargo_to_move)
            # how long did this take
            yield self.env.timeout(load_time)



class Ship(dtv_backend.logbook.HasLog):
    def __init__(self, env, name=None, geometry=None, level=0, capacity=1, speed=1, climate=None, **kwargs):
        super().__init__(env=env)
        self.name = name
        self.geometry = shapely.geometry.shape(geometry)
        self.cargo = simpy.Container(self.env, init=level, capacity=capacity)
        self.speed = speed
        # TODO: where to put this...
        self.climate = climate
        self.metadata = kwargs

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        # independent of trip
        return self.cargo.capacity - self.cargo.level



    def get_max_cargo_for_trip(self, origin, destination, lobith_discharge):
        """determin max cargo to take on a trip, given the discharge at lobith"""

        # TODO: move this out of here?
        max_draught = dtv_backend.fis.determine_max_draught_on_path(
            self.env.FG,
            origin,
            destination,
            lobith_discharge,
            underkeel_clearance=0.30
        )
        draught_full = self.metadata["Draught loaded [m]"]
        draught_empty = self.metadata["Draught empty [m]"]
        try:
            if max_draught > draught_full:
                return self.cargo.capacity
            if max_draught < draught_empty:
                return 0
        except:
            logging.exception("TODO Fix this")
            pass


        max_height = dtv_backend.fis.determine_max_height_on_path(
            self.env.FG,
            origin,
            destination,
            lobith_discharge
        )
        max_layers = dtv_backend.fis.determine_max_layers(max_height)

        # TODO: separate function for container vs bulk ship
        capacity = self.cargo.capacity
        containers_per_layer = self.metadata.get('containers_per_layer', 87)

        # max cargo under height limitation
        max_cargo_height = max_layers * containers_per_layer

        if max_cargo_height > capacity:
            max_cargo_height = capacity

        load_frac_draught = (max_draught - draught_empty) / (draught_full - draught_empty)

        max_cargo_draught = self.cargo.capacity * load_frac_draught

        try:
            max_cargo = min(max_cargo_height, max_cargo_draught)
        except:
            logging.exception("TODO: fix this")
            print(max_cargo_height)
            max_cargo = max_cargo_height
        return max_cargo

    @property
    def node(self):
        node, dist = dtv_backend.fis.find_closest_node(self.env.FG, self.geometry)
        return node

    def load_at(self, port, max_load=None):
        """
        The load_at process can occur after a ship arrives at a port (port).

        It requests a a crane and when available, it moves an amount of cargo to the ship.
        It waits for this to finish and then releases the crane.

        """
        with self.log(
                message="Load request",
                description=f"Load request ({port.name})",
                ship=self,
                crane=port.crane,
                geometry=self.geometry
        ):
            with port.crane.request() as request:
                # wait for the crane to become available
                yield request
                # load the cargo
                yield self.env.process(port.load(port, self, max_load))

    def unload_at(self, port):
        """
        The load_at process can occur after a ship arrives at a port (port).

        It requests a a crane and when available, it moves an amount of cargo to the ship.
        It waits for this to finish and then releases the crane.

        """
        with self.log(
                message="Unload request",
                description=f"Unload request ({port.name})",
                ship=self,
                crane=port.crane,
                geometry=self.geometry
        ):
            with port.crane.request() as request:
                # wait for the crane to become available
                yield request
                # load the cargo
                yield self.env.process(port.load(self, port))

    def move_to(self, destination, limited=False):
        """Move ship to location"""
        graph = self.env.FG
        if limited:
            width = self.metadata['Beam [m]']
            length = self.metadata['Length [m]']
            depth = self.metadata['Draught loaded [m]']
            height = self.metadata['Height average [m]']
            # TODO: validate network dimensions (Duisburg was not reached with Vb)
            path = dtv_backend.fis.shorted_path_by_dimensions(
                graph,
                self.node,
                destination.node,
                width,
                height,
                depth,
                length
            )
        else:
            path = dtv_backend.fis.shorted_path(
                graph,
                self.node,
                destination.node
            )
        total_distance = 0
        for edge in zip(path[:-1], path[1:]):
            distance = graph.edges[edge]['length_m']
            total_distance += distance


        if path:
            # move to destination
            end_node = graph.nodes[path[-1]]
            self.geometry = end_node['geometry']

            if len(path) < 2:
                path_geometry = self.geometry
            else:
                # extrect the geometry
                path_df = dtv_backend.network.network_utilities.path2gdf(path, graph)
                # convert to single linestring
                path_geometry = shapely.ops.linemerge(path_df['geometry'].values)

                start_point = graph.nodes[path_df.iloc[0]['start_node']]['geometry']
                end_point = graph.nodes[path_df.iloc[1]['end_node']]['geometry']
                first_path_point = shapely.geometry.Point(path_geometry.coords[0])
                start_distance = start_point.distance(first_path_point)
                end_distance = end_point.distance(first_path_point)
                if start_distance > end_distance:
                    # invert geometry
                    path_geometry = shapely.geometry.LineString(path_geometry.coords[::-1])

            with self.log(
                    message="Sailing",
                    description=f"Sailing ({self.name})",
                    ship=self,
                    geometry=path_geometry,
                    value=total_distance,
                    path=path
            ):
                yield self.env.timeout(total_distance / self.speed)

    def load_move_unload(self, source, destination, max_load=None):
        """do a full A to B cycle"""
        with self.log(message="Cycle", description="Load move unload cycle"):
            # Don't sail to empty source
            if source.cargo.level > 0:
                yield from self.move_to(source)

                # determine what the cargo to take
                # TODO: move to separate function/prop
                if (self.climate):
                    lobith_discharge = self.climate['discharge']
                    max_cargo_for_trip = self.get_max_cargo_for_trip(
                        source,
                        destination,
                        lobith_discharge
                    )
                    # take the minumum of what was requested and what we can take
                    max_cargo_for_trip = min(max_load, max_cargo_for_trip)
                else:
                    #
                    max_cargo_for_trip = max_load
                yield from self.load_at(source, max_cargo_for_trip)

            # Don't sail empty
            if self.cargo.level > 0:
                yield from self.move_to(destination)
                yield from self.unload_at(destination)

    def work_for(self, operator):
        """Work for an operator by listening to tasks"""
        while True:
            # Get event for message pipe
            task = yield operator.get_task()
            # Where to get the cargo
            source = task.get('source')
            # Where to take it
            destination = task.get('destination')
            # How much
            max_load = task.get('max_load')

            # TODO: consider notifying the operator on progress
            # Notify operator of load changes so extra tasks can be planned
            # operator.send_message() or something...
            yield from self.load_move_unload(source, destination, max_load)
