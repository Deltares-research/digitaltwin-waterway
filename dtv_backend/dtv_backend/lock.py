"""This file contains several functions that are used to mimic lock behaviour in the graph"""

import re
import simpy
import simpy.resources
import requests
import io
import geopandas as gpd

# Define a regular expression to match the lock edges
PAT = re.compile(r"L(?P<id>.+)_(?P<side>.+)")

# Define the URL to the lock information
URL_LOCK_INFO = (
    "https://zenodo.org/records/6673604/files/FIS_locks_grouped.geojson?download=1"
)


class Lock:
    """Class to save lock info."""

    def __init__(self, env, name, lock_resource, lock_container, queue1, queue2):
        """Initialize the Lock class."""
        # Store the lock info
        self.env = env
        self.name = name
        self.lock_resource = lock_resource
        self.lock_container = lock_container
        self.queue1 = queue1
        self.queue2 = queue2

        # define entry 1 or entry 2 open
        self.entry1 = self.env.event()
        self.entry1.succeed("Open")
        self.entry2 = self.env.event()

    def switch_status(self, vessel):
        if self.entry1.triggered and not self.entry2.triggered:
            # switch status from entry 1 to entry 2
            f"{self.env.now:6.1f} s: {self.name} closed entry 1"
            self.entry1 = self.env.event()
            yield self.env.timeout(30 * 60)
            self.entry2.succeed("Open")
            f"{self.env.now:6.1f} s: {self.name} opens entry 2"
        elif self.entry2.triggered and not self.entry1.triggered:
            # switch status from entry 1 to entry 2
            f"{self.env.now:6.1f} s: {self.name} closed entry 2"
            self.entry2 = self.env.event()
            yield self.env.timeout(30 * 60)
            self.entry1.succeed("Open")
            f"{self.env.now:6.1f} s: {self.name} opens entry 1"
        else:
            print(
                f"we should not be here: {self.entry1.triggered} and {self.entry2.triggered}"
            )


class Locks:
    """Class to handle lock passings.

    Initialize this class once.
    Use the pass_lock_v1 function to pass a lock.
    All lock resources are stored in the locks_resources attribute.

    Attributes
    ----------
    env : simpy.Environment
        The simpy environment.
    locks_gdf : geopandas.GeoDataFrame
        The GeoDataFrame containing the lock information.
    locks_resources : dict
        A dictionary containing the lock resources. Maps from lock name to lock resource.
    """

    def __init__(self, env, url_lock_info=URL_LOCK_INFO):
        """Initialize the Locks class."""
        # Store the environment
        self.env = env

        # create lock resources
        self.locks_resources = {}

        # Get lock gdf
        resp = requests.get(url_lock_info)
        stream = io.BytesIO(resp.content)
        self.locks_gdf = gpd.read_file(stream)

    def pass_lock_simple(self, origin, destination, vessel, pat=PAT):
        """simple function which mimics the passing of a lock.
        The passing of a lock simply takes 30 minutes.

        Parameters
        ----------
        origin : str
            The origin of the edge.
        destination : str
            The destination of the edge.
        env : simpy.Environment
            The simpy environment.

        Yields
        ---------
        env.timeout
            The time it takes to pass the lock.
        """
        # Check if the origin and destination are lock edges
        match_origin = re.match(pat, origin)
        match_destination = re.match(pat, destination)

        # If the origin and destination are not lock edges, no timeout is needed.
        if match_origin is None or match_destination is None:
            yield self.env.timeout(0)
            # print('pass edge', origin, destination)
        else:
            # TODO in het logboek toevoegen dat de boot een sluis passeert
            print("pass lock", origin, destination)
            yield self.env.timeout(
                30 * 60
            )  # TODO De normale timeout wordt hier ook bij opgeteld. Dat willen we niet.

    def pass_lock_v2(self, origin, destination, vessel, pat=PAT):
        """simple function which mimics the passing of a lock.

        Parameters
        ----------
        origin : str
            The origin of the edge.
        destination : str
            The destination of the edge.
        env : simpy.Environment
            The simpy environment.

        Yields
        ---------
        env.timeout
            The time it takes to pass the lock.
        """
        # Check if the origin and destination are lock edges
        match_origin = re.match(pat, origin)
        match_destination = re.match(pat, destination)

        # If the origin and destination are not lock edges, no timeout is needed.
        if match_origin is None or match_destination is None:
            yield self.env.timeout(0)

        else:
            # TODO in het logboek toevoegen dat de boot een sluis passeert
            lock = self.get_lock_resource(name=match_origin.group("id"))
            # if match_origin.group("side") < match_origin.group("side"):
            self.env.process(self.pass_lock_1_2(lock, vessel, origin))

            # else:
            #     self.env.process(self.pass_lock_2_1(lock, vessel, origin))

    def pass_lock_1_2(self, lock: Lock, vessel, origin):
        # access que to lock
        with lock.queue1.request() as req:
            yield req  # TODO request length of vessel
            print(f"{self.env.now:6.1f} s: {vessel.name} entered queue1 of {origin}")

        # access lock
        with lock.lock_resource.request() as req:
            # request if there is still space in the lock
            yield req
            print(f"{self.env.now:6.1f} s: {vessel.name} may join lock coming switch")

            # wait untill entry 1 is open
            yield lock.entry1
            print(f"{self.env.now:6.1f} s: {vessel.name} accesses lock")

            # wait untill entry 2 is open
            yield lock.entry2
            print(f"{self.env.now:6.1f} s: {vessel.name} leaves lock")

    def pass_lock_2_1(self, lock: Lock, vessel, origin):
        # access que to lock
        with lock.queue2.request() as req:
            yield req  # TODO request length of vessel
            print(f"{self.env.now:6.1f} s: {vessel.name} entered queue1 of {origin}")

        # access lock
        with lock.lock_resource.request() as req:
            yield req
            print(f"{self.env.now:6.1f} s: {vessel.name} accessed lock")

            self.env.process(lock.switch_status())
            print(f"{self.env.now:6.1f} s: {vessel.name} leaves lock")

    def lock_control(self, lock: Lock):
        """Check if lock is open and at right side

        Parameters
        ----------
        lock : _type_
            _description_
        """
        while True:
            # if entry one of lock is open:
            if lock.entry1.triggered:
                # move lock when queue is empty or when lock is full
                if (
                    lock.queue1.count == 0 and lock.queue2.count > 0
                ) or lock.lock_resource.count == lock.lock_resource.capacity:
                    print(f"{self.env.now:6.1f} s: {lock.name} closes entry 1")
                    lock.entry1 = self.env.event()
                    yield self.env.timeout(30 * 60)
                    lock.entry2.succeed("Open")
                    print(f"{self.env.now:6.1f} s: {lock.name} opens entry 2")
                    # blijf 5 minuten open
                    yield self.env.timeout(5 * 60)

            elif lock.entry2.triggered:
                # move lock when queue2 is empty and queue1 not, or when lock is full
                if (
                    lock.queue2.count == 0 and lock.queue1.count > 0
                ) or lock.lock_resource.count == lock.lock_resource.capacity:
                    print(f"{self.env.now:6.1f} s: {lock.name} closes entry 2")
                    lock.entry2 = self.env.event()
                    # wisselen van positie kost 30 minuten.
                    yield self.env.timeout(30 * 60)
                    lock.entry1.succeed("Open")
                    print(f"{self.env.now:6.1f} s: {lock.name} opens entry 1")
                    # blijf 5 minuten open
                    yield self.env.timeout(5 * 60)
            # check every 5 minutes
            yield self.env.timeout(60)

    def get_lock_resource(self, name):
        """get or create a lock resource.

        Parameters
        ----------
        name: str
            The name of the lock.
        Returns
        -------
        Lock
            Lock: The lock resource.
        """
        if name not in self.locks_resources:
            lock = self.make_lock_resource(name)
            self.locks_resources[name] = lock
        else:
            lock = self.locks_resources[name]
        return lock

    def make_lock_resource(self, name):
        """Make a lock resource.

        Parameters
        ----------
        name: str
            The name of the lock.
        Returns
        -------
        simpy.Resource
            lock: The lock resource.
        simpy.Resource
            queue1 : The queue for the first side of the lock.
        simpy.Resource
            queue2 : The queue for the second side of the lock.

        """
        # get length of lock
        name = int(name)
        length = self.locks_gdf[self.locks_gdf["Id"] == name].Length_chamber.values[0]
        # TODO get other info on lock. For now only length is used
        lock_resource = simpy.Resource(
            env=self.env, capacity=2
        )  # TODO capacity = length
        lock_container = simpy.Container(env=self.env, init=0, capacity=length)

        queue1 = simpy.Resource(env=self.env, capacity=999)
        queue2 = simpy.Resource(env=self.env, capacity=999)
        lock = Lock(
            env=self.env,
            name=name,
            lock_resource=lock_resource,
            lock_container=lock_container,
            queue1=queue1,
            queue2=queue2,
        )
        self.env.process(self.lock_control(lock))
        return lock


if __name__ == "__main__":
    import datetime
    import time
    import opentnsim.core as core
    import networkx as nx
    from dtv_backend.fis import load_fis_network
    import functools
    import pandas as pd

    def start(env, vessel):
        while True:
            vessel.log_entry_v0("Start sailing", env.now, "", vessel.geometry)
            yield from vessel.move()
            vessel.log_entry_v0("Stop sailing", env.now, "", vessel.geometry)

            if (
                vessel.geometry
                == nx.get_node_attributes(env.FG, "geometry")[vessel.route[-1]]
            ):
                break

    # start environment
    simulation_start = datetime.datetime.now()
    env = simpy.Environment()

    # make graph
    url = "https://zenodo.org/record/6673604/files/network_digital_twin_v0.3.pickle?download=1"
    env.FG = load_fis_network(url).copy()

    # make locks
    locks = Locks(env)

    # make vessel
    route_langs_twee_locks = nx.dijkstra_path(env.FG, "B7937_B", "8860920")
    TransportResource = type(
        "TransportResource",
        (
            core.Identifiable,
            core.Movable,
            core.HasResource,
            core.Routable,
            core.VesselProperties,
            core.ExtraMetadata,
        ),
        {},
    )
    vessels = []
    for i in [0, 1, 2]:
        vessel = TransportResource(
            **{
                "env": env,
                "name": f"vessel_test{i}",
                "type": "M6",
                "B": 1,
                "L": 10,
                "route": route_langs_twee_locks,
                "geometry": env.FG.nodes["B7937_B"]["geometry"],  # lon, lat
                "capacity": 10,
                "v": 1,
            }
        )
        # add lock
        filled_pass_lock = functools.partial(locks.pass_lock_v2, vessel=vessel)
        vessel.on_pass_edge_functions = [filled_pass_lock]

        # append vessel
        vessels.append(vessel)

    # process vessels
    for vessel in vessels:
        env.process(start(env, vessel))

    # run simulation
    env.run(until=60 * 60 * 24)
    pd.DataFrame(vessel.logbook)
