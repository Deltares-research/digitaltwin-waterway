"""This file contains several functions that are used to mimic lock behaviour in the graph

The lock module can be used to include a simple imitation of locks in the simulation. 

Example of usage: 
#    create locks module with the right environment.
locks = Locks(env)
#   add the pass_lock function to the on_pass_edge_functions of the vessel(s)
filled_pass_lock = functools.partial(locks.pass_lock, vessel=vessel)
vessel.on_pass_edge_functions = [filled_pass_lock]
"""

import re
import simpy
import simpy.events
import simpy.resources
import requests
import io
import geopandas as gpd
import numpy as np
import opentnsim.core as core
from dtv_backend.lock_packing import fill_lock
from typing import Tuple

# Define a regular expression to match the lock edges
PAT = re.compile(r"L(?P<id>.+)_(?P<side>.+)")

# Define the URL to the lock information
URL_LOCK_INFO = (
    "https://zenodo.org/records/6673604/files/FIS_locks_grouped.geojson?download=1"
)


class VesselInLock:
    """different type of vessel-class needed. Else Filterstore.get(vessel) does not work"""

    def __init__(self, vessel, entrytime):
        self.vessel = vessel
        self.name = vessel.name
        self.L = vessel.L
        self.B = vessel.B
        self.entrytime = entrytime


class Chamber(core.Log):
    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        chamber_resource: simpy.Resource,
        queue_a: simpy.FilterStore,
        queue_b: simpy.FilterStore,
        length_chamber: float,
        width_chamber: float,
        time_to_switch: float = 30 * 60,
        geometry=None,
    ):
        # Initialize the Log class
        super().__init__(env=env)

        # Store the chamber info
        self.geometry = geometry
        self.env = env
        self.name = name
        self.time_to_switch = time_to_switch
        self.length_chamber = length_chamber
        self.width_chamber = width_chamber
        self.chamber_resource = chamber_resource
        self.queue_a = queue_a
        self.queue_b = queue_b

        # define events for entry A or entry B open
        self.entry_a = self.env.event()
        self.entry_a.succeed("Open")
        self.entry_b = self.env.event()

        # vessels that can enter chamber
        self.vessels_in_chamber = {}

        # define that queues are empty. Gets triggered when full
        self.queue_a_nonempty = self.env.event()
        self.queue_b_nonempty = self.env.event()
        self.chamber_nonempty = self.env.event()

        # start lock controlls
        self.env.process(self.chamber_control_a_b())
        self.env.process(self.chamber_control_b_a())
        self.env.process(self.transport_vessels_queue_a_into_chamber())
        self.env.process(self.transport_vessels_queue_b_into_chamber())

    @property
    def state(self):
        """Get the state of the chamber."""
        return {
            "name": self.name,
            "chamber_resource": self.chamber_resource.count,
            "queue_a": len(self.queue_a.items),
            "queue_b": len(self.queue_b.items),
            "entry_a": self.entry_a.triggered,
            "entry_b": self.entry_b.triggered,
        }

    def chamber_control_a_b(self):
        """Moves the chamber up."""
        while True:
            # wait until entry a is open
            yield self.entry_a

            # give vessels a second to leave lock
            yield self.env.timeout(1)
            self._evaluate_queues()

            # wait until vessels are in chamber or in queue b
            yield simpy.AnyOf(
                env=env, events=[self.chamber_nonempty, self.queue_b_nonempty]
            )  # TODO and queue_a is empty

            # close entry A
            self.log_entry_v0(
                f"Closes entry A",
                self.env.now,
                self.state,
                self.geometry,
            )
            self.entry_a = self.env.event()

            # move chamber up/down
            yield self.env.timeout(self.time_to_switch)

            # open entry B
            self.entry_b.succeed("Open")
            self.log_entry_v0(
                f"Opens entry B",
                self.env.now,
                self.state,
                self.geometry,
            )

    def chamber_control_b_a(self):
        """moves the chamber down."""
        while True:
            # wait until entry a is open
            yield self.entry_b

            # give vessels a second to leave chamber
            yield self.env.timeout(1)
            self._evaluate_queues()

            # wait untill vessels in chamber or in queue a
            yield simpy.AnyOf(
                env=env, events=[self.chamber_nonempty, self.queue_a_nonempty]
            )  # TODO and queue_b is empty

            # close entry B
            self.log_entry_v0(
                f"Closes entry B",
                self.env.now,
                self.state,
                self.geometry,
            )
            self.entry_b = self.env.event()

            # move chamber up/down
            yield self.env.timeout(self.time_to_switch)

            # open entry A
            self.entry_a.succeed("Open")
            self.log_entry_v0(
                f"Opens entry A",
                self.env.now,
                self.state,
                self.geometry,
            )

    def _evaluate_queues(self):
        """Checks and updates the status of events for the queues and lock_resource."""
        # check and update status queue a
        if len(self.queue_a.items) == 0 and self.queue_a_nonempty.triggered:
            self.queue_a_nonempty = self.env.event()
        elif len(self.queue_a.items) > 0 and not self.queue_a_nonempty.triggered:
            self.queue_a_nonempty.succeed("queue a not empty")

        # check and update status queue b
        if len(self.queue_b.items) == 0 and self.queue_b_nonempty.triggered:
            self.queue_b_nonempty = self.env.event()
        elif len(self.queue_b.items) > 0 and not self.queue_b_nonempty.triggered:
            self.queue_b_nonempty.succeed("queue b not empty")

        # check and update status chamber resource
        if self.chamber_resource.count == 0 and self.chamber_nonempty.triggered:
            self.chamber_nonempty = self.env.event()
        elif self.chamber_resource.count > 0 and not self.chamber_nonempty.triggered:
            self.chamber_nonempty.succeed("chamber not empty")

    def transport_vessels_queue_a_into_chamber(self):
        """Wait until vessels can enter the chamber from queue a, and calculate which vessels can enter the chamber."""
        while True:
            # wait until vessels in queue a
            yield self.queue_a_nonempty

            # wait until entry a is open
            yield self.entry_a

            # determine which ships can pass
            vessels_entering_chamber = fill_lock(
                queue=self.queue_a,
                lock_length=self.length_chamber,
                lock_width=self.width_chamber,
            )

            # let ships enter lock. The event triggers lock.lock_resource.request() as req in locks.pass_lock
            for vessel in vessels_entering_chamber:
                self.vessels_in_chamber[vessel.name].succeed("enters chamber")
            self._evaluate_queues()

            # wait a sec for entry a to close
            yield self.env.timeout(2)

    def transport_vessels_queue_b_into_chamber(self):
        """Wait untill vessels can enter the lock from queue b, and calculate which vessels can enter the lock."""
        while True:
            # wait untill vessels in queue b
            yield self.queue_b_nonempty

            # wait untill entry b is open
            yield self.entry_b

            # determine which ships can pass
            vessels_entering_chamber = fill_lock(
                queue=self.queue_b,
                lock_length=self.length_chamber,
                lock_width=self.width_chamber,
            )

            # let ships enter lock. The event triggers lock.lock_resource.request() as req in locks.pass_lock
            for vessel in vessels_entering_chamber:
                self.vessels_in_chamber[vessel.name].succeed("enters lock")
            self._evaluate_queues()

            # wait a sec for entry a to close
            yield self.env.timeout(2)


class Lock(core.Log):
    def __init__(self, env, name, geometry, chambers: list[Chamber]):
        """Initialize the Lock class.

        Parameters
        ----------
        chambers : dict
            A dictionary containing the lock chambers. Has items 'name', 'length', 'width', 'time to switch'.
        """
        # Initialize the Log class
        super().__init__(env=env)

        self.env = env
        self.chambers = chambers
        self.name = name
        self.geometry = geometry

    def vessel_to_correct_chamber(
        self, entry_side
    ) -> Tuple[Chamber, simpy.FilterStore]:
        """determines which chamber and which queue the vessel should enter.

        The vessel will enter the chamber in the lock, with the shortest queue (in number of vessels). TODO This function can be optimized further...
        """

        if entry_side == "A":
            # find shortst queue on 'a' side
            lengths = [len(chamber.queue_a.items) for chamber in self.chambers]
            chamber = self.chambers[np.argmin(lengths)]
            entry_queue = chamber.queue_a
        elif entry_side == "B":
            # find shortst queue on 'b' side
            lengths = [len(chamber.queue_b.items) for chamber in self.chambers]
            chamber = self.chambers[np.argmin(lengths)]
            entry_queue = chamber.queue_b
        else:
            raise ValueError("ERROR: side of lock not found")

        # return chamber and entry_queue
        return chamber, entry_queue


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

    def __init__(self, env, url_lock_info=URL_LOCK_INFO, schuttijden: dict = {}):
        """Initialize the Locks class."""
        # Store the environment
        self.env = env

        # create lock resources
        self.locks_resources = {}

        # Get lock gdf, with info on chambers of each lock
        resp = requests.get(url_lock_info)
        stream = io.BytesIO(resp.content)
        self.locks_gdf = gpd.read_file(stream)
        self.schuttijden = schuttijden

    def pass_lock(self, origin, destination, vessel, pat=PAT):
        """function which mimics the passing of a lock.

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
                    )
                )
            elif match_origin.group("side") == "B":
                yield self.env.process(
                    self._pass_lock_A_B(
                        lock,
                        vessel,
                        entry_side="B",
                        origin=origin,
                    )
                )
            else:
                print("ERROR: side of lock not found")

    def _pass_lock_A_B(
        self,
        lock: Lock,
        vessel,
        entry_side,
        origin,
    ):
        """Put vessel in queue, wait until vessel can enter lock, and let vessel pass lock.

        Yields:
        -------
        The time it takes for the vessel to pass the lock.
        """
        # define exit side
        if entry_side == "A":
            exit_side = "B"
        elif entry_side == "B":
            exit_side = "A"
        else:
            print("ERROR: side of lock not found")

        # define entry queue and put in queue
        chamber, entry_queue = lock.vessel_to_correct_chamber(entry_side=entry_side)
        yield entry_queue.put(VesselInLock(vessel, self.env.now))

        # create event for vessel to enter lock
        chamber._evaluate_queues()
        chamber.vessels_in_chamber[vessel.name] = self.env.event()

        # logbook vessel
        vessel.log_entry_v0(
            f"Start waiting for lock {origin}, chamber {chamber.name}",
            self.env.now,
            f"",
            vessel.geometry,
        )

        # lockbook chamber.
        lock.log_entry_v0(
            f"{vessel.name} enters queue for chamber {chamber.name}",
            self.env.now,
            chamber.state,
            lock.geometry,
        )

        # wait until the vessel can enter the lock
        yield chamber.vessels_in_chamber[vessel.name]

        # remove vessel from queue
        yield entry_queue.get(lambda x: x.vessel == vessel)

        # access lock
        with chamber.chamber_resource.request() as req:
            yield req
            chamber._evaluate_queues()
            # logbook
            vessel.log_entry_v0(
                f"Passing lock {entry_side} start", self.env.now, "", vessel.geometry
            )
            lock.log_entry_v0(
                f"{vessel.name} enters chamber {chamber.name}",
                self.env.now,
                chamber.state,
                lock.geometry,
            )

            # wait untill entry 2 is open
            if entry_side == "A":
                yield chamber.entry_b
            elif entry_side == "B":
                yield chamber.entry_a

            vessel.log_entry_v0(
                f"Passing lock {entry_side} stop", self.env.now, "", vessel.geometry
            )
            lock.log_entry_v0(
                f"{vessel.name} leaves lock", self.env.now, chamber.state, lock.geometry
            )

            chamber.vessels_in_chamber.pop(vessel.name)
            chamber._evaluate_queues()

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
        # get length of lock #TODO lengte en schuttijd mee kunnen geven per kolk
        name = int(name)
        length = self.locks_gdf[self.locks_gdf["Id"] == name].Length_chamber.values[0]
        width = self.locks_gdf[self.locks_gdf["Id"] == name].Width_chamber.values[0]
        if name in self.schuttijden.keys():
            schuttijd = self.schuttijden[name]
        else:
            schuttijd = 30 * 60

        n_chambers = int(
            self.locks_gdf[self.locks_gdf["Id"] == name].NumberOfChambers.values[0]
        )
        chambers = []
        for i in range(n_chambers):
            chamber = Chamber(
                env=self.env,
                name=f"{name}_{i}",
                chamber_resource=simpy.Resource(env=self.env, capacity=np.inf),
                queue_a=simpy.FilterStore(env=self.env),
                queue_b=simpy.FilterStore(env=self.env),
                length_chamber=length,
                width_chamber=width,
                time_to_switch=schuttijd,
                geometry=self.locks_gdf[self.locks_gdf["Id"] == name].geometry.values[
                    0
                ],
            )
            chambers.append(chamber)

        lock = Lock(
            env=self.env,
            name=name,
            geometry=self.locks_gdf[self.locks_gdf["Id"] == name].geometry.values[0],
            chambers=chambers,
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
    widths = [6, 7, 5, 3]  # lock width is 14
    lengths = [80, 50, 50, 70]  # lock length is 110
    for i in [0, 1, 2, 3]:
        vessel = TransportResource(
            **{
                "env": env,
                "name": f"vessel_test{i}",
                "type": "M6",
                "B": widths[i],
                "L": lengths[i],
                "route": route_langs_twee_locks,
                "geometry": env.FG.nodes["B7937_B"]["geometry"],  # lon, lat
                "capacity": 10,
                "v": 1,
            }
        )
        vessels.append(vessel)

    for i in [4, 5, 6, 7]:
        vessel = TransportResource(
            **{
                "env": env,
                "name": f"vessel_test{i}",
                "type": "M6",
                "B": 10,
                "L": 150,
                "route": route_langs_twee_locks[-1:0:-1],
                "geometry": env.FG.nodes["8860920"]["geometry"],  # lon, lat
                "capacity": 10,
                "v": 1,
            }
        )
        vessels.append(vessel)

    for vessel in vessels:
        filled_pass_lock = functools.partial(locks.pass_lock, vessel=vessel)
        vessel.on_pass_edge_functions = [filled_pass_lock]

    # process vessels
    for vessel in vessels:
        env.process(start(env, vessel))

    # run simulation
    env.run(until=500 * 60 * 24)
    pd.DataFrame(vessel.logbook)
    lock = locks.locks_resources["12784"]
    # import pickle

    # pickle.dump(lock.logbook, open("locks.pickle", "wb"))
    # pickle.load(open("locks.pickle", "rb"))
    logbook = pd.DataFrame(lock.logbook)
    for chamber in lock.chambers:
        logbook_chamber = pd.DataFrame(chamber.logbook)
        logbook = pd.concat([logbook, logbook_chamber], axis=0)
    logbook = logbook.sort_values(by="Timestamp").reset_index(drop=True)
    lock_properties = pd.DataFrame(logbook["Value"].values.tolist())
    pd.concat([logbook, lock_properties], axis=1)
