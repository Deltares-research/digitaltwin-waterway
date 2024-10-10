"""This file contains several functions that are used to mimic lock behaviour in the graph"""

import re
import simpy
import simpy.events
import simpy.resources
import requests
import io
import geopandas as gpd
import numpy as np
import opentnsim.core as core

# Define a regular expression to match the lock edges
PAT = re.compile(r"L(?P<id>.+)_(?P<side>.+)")

# Define the URL to the lock information
URL_LOCK_INFO = (
    "https://zenodo.org/records/6673604/files/FIS_locks_grouped.geojson?download=1"
)

AVERAGE_SHIP_LENGTH = 50  # m


class Lock(core.Log):
    """Class to save lock info."""

    def __init__(
        self,
        geometry,
        env,
        name,
        lock_resource,
        lock_container,
        queue_a,
        queue_b,
        time_to_switch=30 * 60,
        *args,
        **kwargs,
    ):
        """Initialize the Lock class."""
        # Initialize the Log class
        super().__init__(env=env, *args, **kwargs)

        # Store the lock info
        self.geometry = geometry
        self.env = env
        self.name = name
        self.time_to_switch = time_to_switch
        self.lock_resource = lock_resource
        self.lock_container = lock_container
        self.queue_a = queue_a
        self.queue_b = queue_b

        # define entry A or entry B open
        self.entry_a = self.env.event()
        self.entry_a.succeed("Open")
        self.entry_b = self.env.event()

        self.env.process(self.lock_control())

    @property
    def state(self):
        """Get the state of the lock."""
        return {
            "name": self.name,
            "lock_resource": self.lock_resource.count,
            "lock_container": self.lock_container.level,
            "queue_a": self.queue_a.count,
            "queue_b": self.queue_b.count,
            "entry_a": self.entry_a.triggered,
            "entry_b": self.entry_b.triggered,
        }

    def lock_control(self):
        """Moves the lock up and down."""
        while True:
            # entry a is triggered if entry a is open
            if self.entry_a.triggered:
                # move lock when queue_a is empty and queue_b not,
                # or when queue a  is empty and someone is in the lock
                # or when lock is full
                if (
                    (self.queue_a.count == 0 and self.queue_b.count > 0)
                    or (self.lock_resource.count == self.lock_resource.capacity)
                    or (self.lock_resource.count > 0 and self.queue_a.count == 0)
                ):
                    # close entry A
                    self.log_entry_v0(
                        f"Closes entry A",
                        self.env.now,
                        self.state,
                        self.geometry,
                    )
                    self.entry_a = self.env.event()
                    # move lock
                    yield self.env.timeout(self.time_to_switch)
                    # open entry B
                    self.entry_b.succeed("Open")
                    self.log_entry_v0(
                        f"Opens entry B",
                        self.env.now,
                        self.state,
                        self.geometry,
                    )
                    # blijf 1 minuut open
                    yield self.env.timeout(60)
            # entry b is triggered if entry b is open
            elif self.entry_b.triggered:
                # move lock when queue_b is empty and queue_a not,
                # or when queue b is empty and someone is in the lock
                # or when lock is full
                if (
                    (self.queue_b.count == 0 and self.queue_a.count > 0)
                    or (self.lock_resource.count == self.lock_resource.capacity)
                    or (self.lock_resource.count > 0 and self.queue_b.count == 0)
                ):
                    self.log_entry_v0(
                        f"Closes entry B",
                        self.env.now,
                        self.state,
                        self.geometry,
                    )
                    self.entry_b = self.env.event()
                    # wisselen van positie kost 30 minuten.
                    yield self.env.timeout(self.time_to_switch)
                    self.entry_a.succeed("Open")
                    self.log_entry_v0(
                        f"Opens entry A",
                        self.env.now,
                        self.state,
                        self.geometry,
                    )  # blijf 1 minuut open
                    yield self.env.timeout(60)

            # check every minute
            yield self.env.timeout(60)


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

        # Get lock gdf, with info on chambers of each lock
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
        vessel :
            The vessel that passes the lock.
        pat : re.Pattern
            The regular expression pattern to match the lock edges.
            Needs to contain the groups 'id' and 'side'. default: PAT

        Yields
        ---------
        env.timeout
            The time it takes to pass the lock.
        """
        # if origin and destination are tuples, transform to not-tuple
        if isinstance(origin, tuple):
            origin = origin[1]
            destination = destination[1]

        # Check if the origin and destination are lock edges
        match_origin = re.match(pat, origin)
        match_destination = re.match(pat, destination)

        # If the origin and destination are not lock edges, no timeout is needed.
        if match_origin is None or match_destination is None:
            yield self.env.timeout(0)
            # print('pass edge', origin, destination)
        else:
            # TODO in het logboek toevoegen dat de boot een sluis passeert
            print(
                f"{self.env.now:6.1f} s: {vessel.name} passes lock", origin, destination
            )
            yield self.env.timeout(
                30 * 60
            )  # TODO De normale timeout wordt hier ook bij opgeteld. Dat willen we niet.
            yield self.env.process(self._pass_lock_1_2_simple())

    def pass_lock_v2(self, origin, destination, vessel, pat=PAT):
        """simple function which mimics the passing of a lock.

        Parameters
        ----------
        origin : str
            The origin of the edge.
        destination : str
            The destination of the edge.
        vessel :
            The vessel that passes the lock.
        pat : re.Pattern
            The regular expression pattern to match the lock edges.
            Needs to contain the groups 'id' and 'side'. default: PAT

        Yields
        ---------
        env.timeout
            The time it takes to pass the lock.
        """
        # if origin and destination are tuples, transform to not-tuple
        if isinstance(origin, tuple):
            origin = origin[1]
            destination = destination[1]

        # Check if the origin and destination are lock edges
        match_origin = re.match(pat, origin)
        match_destination = re.match(pat, destination)

        # If the origin and destination are not lock edges, no timeout is needed.
        if match_origin is None or match_destination is None:
            yield self.env.timeout(0)
            # TODO misschien kan hier een return. Dan kan else weg.

        else:
            # TODO in het logboek toevoegen dat de boot een sluis passeert
            lock = self._get_lock_resource(name=match_origin.group("id"))

            # TODO evt op branch van Floor kijken hoe je de afstand*snelheid niet meeneemt.
            # Pass the lock from one side to the other side
            if (
                match_origin.group("side") == "A"
            ):  # TODO kanten koppelen aan queues in dict
                yield self.env.process(
                    self._pass_lock_A_B(
                        lock,
                        vessel,
                        entry_side="A",
                        origin=origin,
                        entry_queue=lock.queue_a,
                    )
                )
            elif match_origin.group("side") == "B":
                yield self.env.process(
                    self._pass_lock_A_B(
                        lock,
                        vessel,
                        entry_side="B",
                        origin=origin,
                        entry_queue=lock.queue_b,
                    )
                )
            else:
                print("ERROR: side of lock not found")

    def _pass_lock_1_2_simple(self):
        yield self.env.timeout(np.random.rand() * 30 * 60)

    def _pass_lock_A_B(self, lock: Lock, vessel, entry_side, origin, entry_queue):
        # access que to lock
        if entry_side == "A":
            exit_side = "B"
        elif entry_side == "B":
            exit_side = "A"
        else:
            print("ERROR: side of lock not found")

        with entry_queue.request() as req:
            yield req  # TODO request length of vessel

            vessel.log_entry_v0(
                f"Start waiting for lock {origin}", self.env.now, f"", vessel.geometry
            )  # wait untill the lock has space, and entry is open.

            if entry_side == "A":
                while (lock.lock_resource.capacity == lock.lock_resource.count) or not (
                    lock.entry_a.triggered
                ):
                    yield self.env.timeout(10)
            if entry_side == "B":
                while (lock.lock_resource.capacity == lock.lock_resource.count) or not (
                    lock.entry_b.triggered
                ):
                    yield self.env.timeout(10)

            vessel.log_entry_v0(
                f"Stop waiting for lock {origin}", self.env.now, f"", vessel.geometry
            )

        # access lock
        with lock.lock_resource.request() as req:
            # Check again if entry is open
            if entry_side == "A":
                yield lock.entry_a
            elif entry_side == "B":
                yield lock.entry_b

            # request lock
            yield req
            vessel.log_entry_v0(
                f"Passing lock {entry_side} start", self.env.now, "", vessel.geometry
            )
            lock.log_entry_v0(
                f"{vessel.name} enters lock", self.env.now, lock.state, lock.geometry
            )

            # wait untill entry 2 is open
            if entry_side == "A":
                yield lock.entry_b
            elif entry_side == "B":
                yield lock.entry_a

            vessel.log_entry_v0(
                f"Passing lock {entry_side} stop", self.env.now, "", vessel.geometry
            )
            lock.log_entry_v0(
                f"{vessel.name} leaves lock", self.env.now, lock.state, lock.geometry
            )

    def _get_lock_resource(self, name):
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
            lock = self._make_lock_resource(name)
            self.locks_resources[name] = lock
        else:
            lock = self.locks_resources[name]
        return lock

    def _make_lock_resource(self, name):
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
            queue_a : The queue for the first side of the lock.
        simpy.Resource
            queue_b : The queue for the second side of the lock.

        """
        # get length of lock
        name = int(name)
        length = self.locks_gdf[self.locks_gdf["Id"] == name].Length_chamber.values[0]
        # TODO get other info on lock. For now only length is used
        capacity = (
            np.floor(length / AVERAGE_SHIP_LENGTH)
            if length > AVERAGE_SHIP_LENGTH
            else 3
        )
        lock_resource = simpy.Resource(
            env=self.env, capacity=capacity
        )  # TODO capacity = length
        lock_container = simpy.Container(env=self.env, init=0, capacity=length)

        queue_a = simpy.Resource(env=self.env, capacity=999)
        queue_b = simpy.Resource(env=self.env, capacity=999)
        lock = Lock(
            geometry=self.locks_gdf[self.locks_gdf["Id"] == name].geometry.values[0],
            env=self.env,
            name=name,
            lock_resource=lock_resource,
            lock_container=lock_container,
            queue_a=queue_a,
            queue_b=queue_b,
        )
        return lock


if __name__ == "__main__":
    import datetime
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
        vessels.append(vessel)

    # for i in [3, 4, 5, 6, 7]:
    #     vessel = TransportResource(
    #         **{
    #             "env": env,
    #             "name": f"vessel_test{i}",
    #             "type": "M6",
    #             "B": 1,
    #             "L": 10,
    #             "route": route_langs_twee_locks[-1:0:-1],
    #             "geometry": env.FG.nodes["8860920"]["geometry"],  # lon, lat
    #             "capacity": 10,
    #             "v": 1,
    #         }
    #     )
    #     vessels.append(vessel)

    for vessel in vessels:
        filled_pass_lock = functools.partial(locks.pass_lock_v2, vessel=vessel)
        vessel.on_pass_edge_functions = [filled_pass_lock]

    # process vessels
    for vessel in vessels:
        env.process(start(env, vessel))

    # run simulation
    env.run(until=500 * 60 * 24)
    pd.DataFrame(vessel.logbook)
    lock = locks.locks_resources["24504"]
    import pickle

    pickle.dump(lock.logbook, open("locks.pickle", "wb"))
    pickle.load(open("locks.pickle", "rb"))
