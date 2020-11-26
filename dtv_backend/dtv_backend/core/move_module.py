# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 14:25:14 2020

@author: KLEF
"""
import pyproj
import shapely.geometry
import networkx as nx
import logging
import datetime, time

import opentnsim.core as TNcore
import openclsim.core as CLcore

logger = logging.getLogger(__name__)

#%% Define a new locatable class
class Locatable:
    """Something with a geometry (geojson format)

    geometry: can be a point as well as a polygon
    
    This is a mix-in of openTNSim and openCLSim Locatable"""

    def __init__(self, geometry, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.geometry = geometry
        self.wgs84 = pyproj.Geod(ellps="WGS84")
        self.node = None

    def is_at(self, locatable, tolerance=100):
        current_location = shapely.geometry.asShape(self.geometry)
        other_location = shapely.geometry.asShape(locatable.geometry)
        _, _, distance = self.wgs84.inv(
            current_location.x, current_location.y, other_location.x, other_location.y
        )

        return distance < tolerance


#%% make a mix-in of the openCLSim and openTNSim HasContainer
class HasContainer(CLcore.HasContainer):
    """
    New HasContainer class based on the CLcore HasContainer, but added the TNSim functionalities
    """
    def __init__(self, compute_v, capacity, level=0, total_requested=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.compute_v = compute_v
        self.wgs84 = pyproj.Geod(ellps="WGS84")
        
    @property
    def is_loaded(self):
        return True if self.container.level > 0 else False
    
    @property
    def filling_degree(self):
        return self.container.level / self.container.capacity


#%% logging of vessel movements
class Log(CLcore.SimpyObject):
    """Log class

    log: log message [format: 'start activity' or 'stop activity']
    t: timestamp
    value: a value can be logged as well
    geometry: value from locatable (lat, lon)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.log = {"Message": [], "Timestamp": [], "Value": [], "Geometry": []}

    def log_entry(self, log, t, value, geometry_log):
        """Log"""
        self.log["Message"].append(log)
        self.log["Timestamp"].append(datetime.datetime.fromtimestamp(t))
        self.log["Value"].append(value)
        self.log["Geometry"].append(geometry_log)

    def get_log_as_json(self):
        json = []
        for msg, t, value, geometry_log in zip(
            self.log["Message"],
            self.log["Timestamp"],
            self.log["Value"],
            self.log["Geometry"],
        ):
            json.append(
                dict(message=msg, time=t, value=value, geometry_log=geometry_log)
            )
        return json


#%% Using this new Locatable class, also the Movable and consequently ContainerDependentMovable must be redefined
# before I used TNcore.Log
# TODO: error op missense ActivityID die mist in de log entry, dat betekent dus dat niet bovenstaande Log wordt gebruikt, maar die van
# openCLSim(!), dus is Log lijkt in Movable helemaal niet gebruikt te worden
class Movable(Locatable, TNcore.Routeable, CLcore.Log):
    """Movable class

    Used for object that can move with a fixed speed
    geometry: point used to track its current location
    v: speed"""

    def __init__(self, v=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.v = v
        self.wgs84 = pyproj.Geod(ellps="WGS84")

    def move(self):
        """determine distance between origin and destination, and
        yield the time it takes to travel it

        Assumption is that self.path is in the right order - vessel moves from route[0] to route[-1].
        """
        self.distance = 0

        # Check if vessel is at correct location - if note, move to location
        if (
            self.geometry
            != nx.get_node_attributes(self.env.FG, "geometry")[self.route[0]]
        ):
            orig = self.geometry
            dest = nx.get_node_attributes(self.env.FG, "geometry")[self.route[0]]

            print("Origin", orig)
            print("Destination", dest)

            # TODO: now it is not sailing using the network.
            self.distance += self.wgs84.inv(
                shapely.geometry.asShape(orig).x,
                shapely.geometry.asShape(orig).y,
                shapely.geometry.asShape(dest).x,
                shapely.geometry.asShape(dest).y,
            )[2]

            yield self.env.timeout(self.distance / self.current_speed)
            self.log_entry("Sailing to start", self.env.now, self.distance, dest)

        # Move over the path and log every step
        for node in enumerate(self.route):
            self.node = node[1]

            origin = self.route[node[0]]
            # TODO: the following line raises an error if the specified path is of length 1
            # could occur in a general case where I want it to sail to some origin, it it is already there
            # then the path consists of one node
            destination = self.route[node[0] + 1]
            edge = self.env.FG.edges[origin, destination]

            if "Lock" in edge.keys():
                queue_length = []
                lock_ids = []

                for lock in edge["Lock"]:
                    queue = 0
                    queue += len(lock.resource.users)
                    queue += len(lock.line_up_area[self.node].users)
                    queue += len(lock.waiting_area[self.node].users) + len(
                        lock.waiting_area[self.node].queue
                    )

                    queue_length.append(queue)
                    lock_ids.append(lock.id)

                lock_id = lock_ids[queue_length.index(min(queue_length))]
                yield from self.pass_lock(origin, destination, lock_id)

            else:
                yield from self.pass_edge_resources(origin, destination)
                yield from self.pass_edge(origin, destination)

            if node[0] + 2 == len(self.route):
                break

        self.geometry = nx.get_node_attributes(self.env.FG, "geometry")[destination]
        logger.debug("  distance: " + "%4.2f" % self.distance + " m")
        logger.debug("  sailing:  " + "%4.2f" % self.current_speed + " m/s")
        logger.debug(
            "  duration: "
            + "%4.2f" % ((self.distance / self.current_speed) / 3600)
            + " hrs"
        )

    def pass_edge(self, origin, destination):
        edge = self.env.FG.edges[origin, destination]
        # compute distance from spherical distance between origin and destination geometry
        orig = self.env.FG.nodes[origin]["geometry"]
        dest = self.env.FG.nodes[destination]["geometry"]
        
        # changes this one to capital {L}ength to get the 'real' distances from the graph
        if 'Length' in edge:
            distance = edge['Length']
        else:

            # TODO: this is the "as the crow fly distance", derive distance from edge geometry
            distance = self.wgs84.inv(
                shapely.geometry.asShape(orig).x,
                shapely.geometry.asShape(orig).y,
                shapely.geometry.asShape(dest).x,
                shapely.geometry.asShape(dest).y,
            )[2]

        self.distance += distance
        #arrival = self.env.now


        # now start sailing
        self.log_entry(
            "Sailing from node {} to node {} start".format(origin, destination),
            self.env.now,
            0,
            orig,
            self.ActivityID,
        )
        yield self.env.timeout(distance / self.current_speed)
        self.log_entry(
            "Sailing from node {} to node {} stop".format(origin, destination),
            self.env.now,
            0,
            dest,
            self.ActivityID,
        )

    def pass_edge_resources(self, origin, destination):
        # If the edge has resources that we need to wait for
        # wait for the resources to become available
        arrival = self.env.now
        edge = self.env.FG.edges[origin, destination]
        # if there is no resource on the edge, we're done
        if not "Resources" in edge.keys():
            # we spent 0 seconds waiting
            yield self.env.timeout(0)
        else:

            with self.env.FG.edges[origin, destination][
                "Resources"
            ].request() as request:
                # wait for the resource to become available
                yield request

                # if the edge was not immediately available log the waiting time
                if arrival != self.env.now:
                    self.log_entry(
                        "Waiting to pass edge {} - {} start".format(
                            origin, destination
                        ),
                        arrival,
                        0,
                        origin,
                    )
                    self.log_entry(
                        "Waiting to pass edge {} - {} stop".format(origin, destination),
                        self.env.now,
                        0,
                        origin,
                    )


    def pass_lock(self, origin, destination, lock_id):
        """Pass the lock"""

        locks = self.env.FG.edges[origin, destination]["Lock"]
        for lock in locks:
            if lock.id == lock_id:
                break

        # Request access to waiting area
        wait_for_waiting_area = self.env.now

        access_waiting_area = lock.waiting_area[origin].request()
        yield access_waiting_area

        if wait_for_waiting_area != self.env.now:
            waiting = self.env.now - wait_for_waiting_area
            self.log_entry(
                "Waiting to enter waiting area start",
                wait_for_waiting_area,
                0,
                self.geometry,
            )
            self.log_entry(
                "Waiting to enter waiting area stop",
                self.env.now,
                waiting,
                self.geometry,
            )

        # Request access to line-up area
        wait_for_lineup_area = self.env.now

        access_line_up_area = lock.line_up_area[origin].request()
        yield access_line_up_area
        lock.waiting_area[origin].release(access_waiting_area)

        if wait_for_lineup_area != self.env.now:
            waiting = self.env.now - wait_for_lineup_area
            self.log_entry(
                "Waiting in waiting area start", wait_for_lineup_area, 0, self.geometry
            )
            self.log_entry(
                "Waiting in waiting area stop", self.env.now, waiting, self.geometry
            )

        # Request access to lock
        wait_for_lock_entry = self.env.now
        access_lock = lock.resource.request(
            priority=-1 if origin == lock.water_level else 0
        )
        yield access_lock

        # Shift water level
        if origin != lock.water_level:
            yield from lock.convert_chamber(self.env, origin)

        lock.line_up_area[origin].release(access_line_up_area)

        if wait_for_lock_entry != self.env.now:
            waiting = self.env.now - wait_for_lock_entry
            self.log_entry(
                "Waiting in line-up area start", wait_for_lock_entry, 0, self.geometry
            )
            self.log_entry(
                "Waiting in line-up area stop", self.env.now, waiting, self.geometry
            )

        # Vessel inside the lock
        self.log_entry("Passing lock start", self.env.now, 0, self.geometry)

        # Shift the water level
        yield from lock.convert_chamber(self.env, destination)

        # Vessel outside the lock
        lock.resource.release(access_lock)
        passage_time = lock.doors_close + lock.operating_time + lock.doors_open
        self.log_entry(
            "Passing lock stop",
            self.env.now,
            passage_time,
            nx.get_node_attributes(self.env.FG, "geometry")[destination],
        )

    @property
    def current_speed(self):
        return self.v


#%%
class ContainerDependentMovable(Movable, CLcore.HasContainer):
    """ContainerDependentMovable class

    Used for objects that move with a speed dependent on the container level
    compute_v: a function, given the fraction the container is filled (in [0,1]), returns the current speed"""

    def __init__(self, compute_v, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Initialization"""
        self.compute_v = compute_v
        self.wgs84 = pyproj.Geod(ellps="WGS84")
    
    @property
    def is_loaded(self):
        return True if self.container.level > 0 else False
    
    @property
    def filling_degree(self):
        return self.container.get_level() / self.container.get_capacity()
    
    @property
    def current_speed(self):
        return self.compute_v(self.container.get_level() / self.container.get_capacity())


