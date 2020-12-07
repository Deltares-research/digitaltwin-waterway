import uuid
import datetime
import itertools

import simpy
import shapely.geometry
from pint import UnitRegistry

import dtv_backend.fis
import dtv_backend.logbook

ureg = UnitRegistry()



class Operator(dtv_backend.logbook.HasLog):
    """This class represents a fleet operator."""
    def __init__(self, env, name='Operator', ships=None):
        super().__init__(env=env)
        self.name = name
        if not ships:
            raise ValueError("Non empty list of ships is required")

        self.fleet = simpy.Store(env, capacity=len(ships))
        # create list of tasks, any ship can pick them up
        self.tasks = simpy.Store(env, capacity=len(ships))
        for ship in ships:
            self.fleet.put(ship)

    def send_task(self, task):
        """return send task request"""
        return self.tasks.put(task)

    def get_task(self):
        """return get task request"""
        return self.tasks.get()

    def plan(self, source, destination):
        """A process which prepares tasks."""
        with self.log(message=f'Plan ({self.name})'):
            total_work = source.cargo.level
            # estimate max_load per task
            max_load = min(
                max(ship.max_load for ship in self.fleet.items),
                source.cargo.level
            )
            # estimate n tasks + 1 reserve
            n_tasks = (total_work // max_load) + 1
            print('max_load', max_load, n_tasks, total_work)
            for i in range(n_tasks):
                if source.cargo.level <= 0:
                    # source port is empty, we're  done
                    break
                # Send out tasks
                with self.log(message=f"Sending task ({self.name})", max_load=max_load):
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
        self.geometry = shapely.geometry.asShape(geometry)
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

        source.cargo.get(cargo_to_move)
        # move it to the destination
        destination.cargo.put(cargo_to_move)
        # how long did this take
        # tonne / (tonne / hour) -> s
        load_time = cargo_to_move * ureg.metric_ton / (self.loading_rate * (ureg.metric_ton / ureg.hour))
        load_time = load_time.to(ureg.second).magnitude
        with self.log(
                message=f"Loading ({source.name}) -> ({destination.name})",
                destination=destination,
                source=source,
                geometry=self.geometry,
                value=source.cargo.level,
                source_level=source.cargo.level,
                destination_level=destination.cargo.level
        ):
            yield self.env.timeout(load_time)



class Ship(dtv_backend.logbook.HasLog):
    def __init__(self, env, name=None, geometry=None, level=0, capacity=1, speed=1, **kwargs):
        super().__init__(env=env)
        self.name = name
        self.geometry = shapely.geometry.asShape(geometry)
        self.cargo = simpy.Container(self.env, init=level, capacity=capacity)
        self.speed = speed
        self.metadata = kwargs

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        # TODO: update with maximum draught
        return self.cargo.capacity - self.cargo.level

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
                message=f"Load request ({port.name})",
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
            message=f"Unload request ({port.name})",
            ship=self,
            crane=port.crane,
            geometry=self.geometry
        ):
            with port.crane.request() as request:
                # wait for the crane to become available
                yield request
                # load the cargo
                yield self.env.process(port.load(self, port))

    def move_to(self, destination):
        """Move ship to location"""
        graph = self.env.FG
        width = self.metadata['Beam [m]']
        length = self.metadata['Length [m]']
        depth = self.metadata['Draught loaded [m]']
        height = self.metadata['Height average [m]']
        path = dtv_backend.fis.shorted_path_by_dimensions(
            graph,
            self.node,
            destination.node,
            width,
            height,
            depth,
            length
        )
        total_distance = 0
        for edge in zip(path[:-1], path[1:]):
            distance = graph.edges[edge]['length']
            total_distance += distance
        if path:
            # move to destination
            end_node = graph.nodes[path[-1]]
            self.geometry = end_node['geometry']
            with self.log(message=f"Sailing ({self.name})", ship=self, geometry=self.geometry, value=total_distance):
                yield self.env.timeout(total_distance / self.speed)

    def load_move_unload(self, source, destination, max_load=None):
        """do a full A to B cycle"""
        with self.log(message="Cycle"):
            yield from self.move_to(source)
            yield from self.load_at(source, max_load)
            yield from self.move_to(destination)
            yield from self.unload_at(destination)

    def work_for(self, operator):
        """Work for an operator by listening to tasks"""
        while True:
            # Get event for message pipe
            task = yield operator.get_task()
            source = task.get('source')
            destination = task.get('destination')
            max_load = task.get('max_load')
            # TODO: consider notifying the operator
            yield from self.load_move_unload(source, destination, max_load)
