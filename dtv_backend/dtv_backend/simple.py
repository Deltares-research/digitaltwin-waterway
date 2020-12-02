import uuid
import datetime

import simpy
import shapely.geometry
from pint import UnitRegistry

import dtv_backend.network.network_utilities

ureg = UnitRegistry()

counter = 0

def log_entry(message=None, timestamp=None, value=None, geometry=None, state=None, **kwargs):
    global counter
    counter += 1
    entry = {
        "Message": message,
        "Timestamp": datetime.datetime.utcfromtimestamp(timestamp),
        "Value": value,
        "geometry": geometry,
        "AcitivityID": counter,
        "ActivityState": state,
        "Meta": kwargs
    }
    return entry


class Port(object):
    """
    A port has a limited number of cranes (num_cranes) and a cargo storage with a capacity (capacity) and a initial level (level) to
    load or unload ships in parallel.

    Ships have to request one of the cranes. When they got one, they
    can load or unload an amount of cargo and wait for it to moved (which
    takes loading rate * min(ship.max_load, available) minutes).

    The port has a geometry, which can be used for navigation purposes.
    """
    def __init__(self, env, name='Port', num_cranes=1, loading_rate=1, level=0, capacity=1, geometry=None, log=None, **kwargs):
        self.env = env
        self.id = str(uuid.uuid4())
        if log is None:
            log = []
        self.log = log
        self.crane = simpy.Resource(env, num_cranes)
        self.loading_rate = loading_rate
        self.cargo = simpy.Container(env, init=level, capacity=capacity)
        self.geometry = shapely.geometry.asShape(geometry)
        self.metadata = kwargs

    @property
    def node(self):
        node, dist = dtv_backend.network.network_utilities.find_closest_node(self.env.FG, self.geometry)
        return node

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        return self.cargo.capacity - self.cargo.level

    def load(self, source, destination):
        """The loading processes. It takes a ``ship`` and loads it."""
        available = source.cargo.level
        requested = destination.max_load
        cargo_to_move = min(available, requested)
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
        self.log.append(log_entry(
            message="Loading",
            destination=destination,
            source=source,
            geometry=self.geometry,
            value=source.cargo.level,
            timestamp=self.env.now,
            state='STARTED',
            source_level=source.cargo.level,
            destination_level=destination.cargo.level
        ))
        yield self.env.timeout(load_time)
        self.log.append(log_entry(
            message="Loading",
            destination=destination,
            source=source,
            geometry=self.geometry,
            value=source.cargo.level,
            timestamp=self.env.now,
            state='STOPPED',
            source_level=source.cargo.level,
            destination_level=destination.cargo.level
        ))



class Ship(object):
    def __init__(self, env, name=None, geometry=None, level=0, capacity=1, speed=1, log=None, **kwargs):
        self.env = env
        self.name = name
        if log is None:
            log = []
        self.geometry = shapely.geometry.asShape(geometry)
        self.cargo = simpy.Container(self.env, init=level, capacity=capacity)
        self.speed = speed
        self.log = log
        self.metadata = kwargs

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        # TODO: update with maximum draught
        return self.cargo.capacity - self.cargo.level

    @property
    def node(self):
        node, dist = dtv_backend.network.network_utilities.find_closest_node(self.env.FG, self.geometry)
        return node

    def load_at(self, port):
        """
        The load_at process can occur after a ship arrives at a port (port).

        It requests a a crane and when available, it moves an amount of cargo to the ship.
        It waits for this to finish and then releases the crane.

        """
        self.log.append(log_entry(
            message="Crane",
            ship=self,
            crane=port.crane,
            geometry=self.geometry,
            timestamp=self.env.now,
            state='REQUEST'
        ))
        with port.crane.request() as request:
            # wait for the crane to become available
            yield request
            # load the cargo
            yield self.env.process(port.load(port, self))
        self.log.append(log_entry(
            message="Crane",
            ship=self,
            crane=port.crane,
            geometry=self.geometry,
            timestamp=self.env.now,
            state='RELEASE'
        ))

    def unload_at(self, port):
        """
        The load_at process can occur after a ship arrives at a port (port).

        It requests a a crane and when available, it moves an amount of cargo to the ship.
        It waits for this to finish and then releases the crane.

        """
        self.log.append(log_entry(
            message="Crane",
            ship=self,
            crane=port.crane,
            geometry=self.geometry,
            timestamp=self.env.now,
            state='REQUEST'
        ))
        with port.crane.request() as request:
            # wait for the crane to become available
            yield request
            # load the cargo
            yield self.env.process(port.load(self, port))
        self.log.append(log_entry(
            message="Crane",
            ship=self,
            crane=port.crane,
            geometry=self.geometry,
            timestamp=self.env.now,
            state='RELEASE'
        ))

    def move_to(self, destination):
        """Move ship to location"""
        graph = self.env.FG
        width = self.metadata['Beam [m]']
        length = self.metadata['Length [m]']
        depth = self.metadata['Draught loaded [m]']
        height = self.metadata['Height average [m]']
        path = dtv_backend.network.network_utilities.shorted_path_by_dimensions(
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
            self.log.append(log_entry(message="Sailing", ship=self, geometry=self.geometry, value=total_distance, timestamp=self.env.now, state='STARTED'))
            yield self.env.timeout(total_distance / self.speed)
            self.log.append(log_entry(message="Sailing", ship=self, geometry=self.geometry, value=total_distance, timestamp=self.env.now, state='STOPPED'))
    def load_move_unload(self, source, destination):
        """do a full A to B cycle"""
        yield from self.move_to(source)
        yield from self.load_at(source)
        yield from self.move_to(destination)
        yield from self.unload_at(destination)
