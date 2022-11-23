#!/usr/bin/env python3
import datetime
import numpy as np
import logging

import opentnsim.core
import shapely.geometry

from pint import UnitRegistry
import opentnsim.core

import dtv_backend.berthing


ureg = UnitRegistry()


logger = logging.getLogger(__name__)


class CanWork(
    dtv_backend.berthing.CanBerth,
    opentnsim.core.HasContainer,
    opentnsim.core.ExtraMetadata,
):
    """Work class for compatability with OpenTNSim. Can work for an operator."""

    def __init__(self, *args, **kwargs):
        """Initialize"""
        # print(super().__init__)
        super().__init__(*args, **kwargs)
        self.quantity_df = None

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        return self.container.capacity - self.container.level

    def get_waterdepth(self, e):
        """get a waterdepth for edge e on the geodataframe with bathymetry and waterlevel information (nap_p50)"""

        assert self.quantity_df is not None, "we need a quantity_df to compute depths"
        quantity_df = self.quantity_df

        # TODO: add sealevel
        #
        #
        # similar to a channel
        default_waterdepth = 6

        # are both source and target in our edge
        idx = np.logical_and(quantity_df.source.isin(e), quantity_df.target.isin(e))
        # lookup the edge
        selected = quantity_df[idx]

        # did we find records
        if not selected.shape[0]:
            # no, return default
            return default_waterdepth

        quantity_row = selected.iloc[0]
        if np.isnan(quantity_row["waterlevel"]) or np.isnan(quantity_row["nap_p5"]):
            return default_waterdepth

        # we found waterlevel and depth, so we can compute the real waterdepth
        waterdepth = quantity_row["waterlevel"] - quantity_row["nap_p50"]
        return waterdepth

    def get_velocity(self, e):
        """get a waterdepth for edge e on the geodataframe with bathymetry and waterlevel information (nap_p50)"""

        assert self.quantity_df is not None, "we need a quantity_df to compute depths"
        quantity_df = self.quantity_df
        # similar to a channel
        default_velocity = 0

        # are both source and target in our edge
        idx = np.logical_and(quantity_df.source.isin(e), quantity_df.target.isin(e))
        # lookup the edge
        selected = quantity_df[idx]

        # did we find records
        if not selected.shape[0]:
            # no, return default
            return default_velocity

        quantity_row = selected.iloc[0]
        if np.isnan(quantity_row["velocity"]):
            return default_velocity

        # we found a velocity
        velocity = quantity_row.velocity

        # Which way is it going?
        # From source to target
        if e[0] == quantity_row.source:
            velocity = velocity
        else:
            # We're going against the flow
            # we're going backward through this edge, velocity should be negative of given velocity
            velocity = -velocity

        return velocity

    def work_for(self, operator, with_berth=False):
        """Work for an operator by listening to tasks"""
        while True:
            # Get event for message pipe
            task = yield operator.get_task()
            # Where to get the cargo
            source = task.get("source")
            # Where to take it
            destination = task.get("destination")
            # How much
            max_load = task.get("max_load")

            # TODO: consider notifying the operator on progress
            # Notify operator of load changes so extra tasks can be planned
            # operator.send_message() or something...
            yield from self.load_move_unload(
                source, destination, max_load, with_berth=with_berth
            )

    def load_at(self, port, max_load=None):
        """
        The load_at process can occur after a ship arrives at a port (port).

        It requests a a crane (resource) and when available, it moves an amount of cargo to the ship.
        It waits for this to finish and then releases the crane.

        """
        with self.log_context(
            message="Load request",
            description=f"Load request ({port.name})",
            ship=self,
            resource=port.resource,
            geometry=self.geometry,
        ):
            with port.resource.request() as request:
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
        with self.log_context(
            message="Unload request",
            description=f"Unload request ({port.name})",
            ship=self,
            resource=port.resource,
            geometry=self.geometry,
        ):
            with port.resource.request() as request:
                # wait for the crane to become available
                yield request
                # load the cargo
                yield self.env.process(port.load(self, port))

    def load_move_unload(self, source, destination, max_load=None, with_berth=False):
        """do a full A to B cycle"""
        with self.log_context(message="Cycle", description="Load move unload cycle"):
            # Don't sail to empty source
            if source.container.level <= 0:
                return

            if not with_berth:
                yield from self.move_to(source)
            else:
                yield from self.move_to_with_berth(source)
            # determine what the cargo to take
            cargo_for_trip = self.container.capacity
            yield from self.load_at(source, cargo_for_trip)

            # Don't sail empty
            if self.container.level <= 0:
                return

            if not with_berth:
                yield from self.move_to(destination)
            else:
                yield from self.move_to_with_berth(destination)

            yield from self.unload_at(destination)

    def move_to(self, destination, limited=False):
        """Move ship to location"""
        graph = self.env.FG
        if limited:
            width = self.metadata["Beam [m]"]
            length = self.metadata["Length [m]"]
            depth = self.metadata["Draught loaded [m]"]
            height = self.metadata["Height average [m]"]
            # TODO: validate network dimensions (Duisburg was not reached with Vb)
            path = dtv_backend.fis.shorted_path_by_dimensions(
                graph, self.node, destination.node, width, height, depth, length
            )
        else:
            if hasattr(destination, "node"):
                # TODO: rename to shortest_path
                path = dtv_backend.fis.shorted_path(graph, self.node, destination.node)
            elif isinstance(destination, str):
                path = dtv_backend.fis.shorted_path(graph, self.node, destination)
            else:
                raise ValueError(
                    f"destination has no node and is not a string: {destination}"
                )
        if not path:
            raise ValueError(f"We need a path to move on {self}")

        total_distance = 0
        total_duration = 0
        # TODO: move to on_pass_edge
        energy_profile = []
        for e in zip(path[:-1], path[1:]):
            edge = graph.edges[e]
            distance = edge["length_m"]

            # TODO: move this part to on_pass_edge_func
            # compute power used to pass this edge
            # use energy module from opentnsim to compute emissions
            emissions = {}
            timestamp = self.env.now

            depth = self.get_waterdepth(e)
            velocity = self.get_velocity(e)

            # # estimate 'grounding speed' as a useful upperbound
            try:
                (
                    upperbound,
                    selected,
                    results_df,
                ) = opentnsim.strategy.get_upperbound_for_power2v(
                    self, width=150, depth=depth, margin=0
                )
            except:
                upperbound = None
                logger.warn(f"Could not compute upperbound for e {e}")
            v = self.power2v(self, edge, upperbound, h_0=depth)

            # true ship velocity - water velocity
            v = v - velocity

            # sail at least 0.1 m/s
            v = max(v, 0.1)

            # TODO: add some warning if we get below 0.1m/s
            # sail at least 0.1 m / s
            # v = min(v, 0.1)

            # # use computed power
            power_given = self.P_given

            # duration in s
            duration = distance / v
            # keep duration if not sailing at constant speed
            total_duration += duration

            # energy used over edge W(s /  s/h -> s * h /s -> h) -> Wh
            energy = power_given * (duration / 3600)

            self.calculate_total_resistance(v, h_0=depth)
            self.calculate_total_power_required(v=v, h_0=depth)

            self.calculate_emission_factors_total(v=v, h_0=depth)
            self.calculate_SFC_final(v=v, h_0=depth)

            delta_diesel_C_year = self.final_SFC_diesel_C_year_ICE_mass * energy  # in g
            delta_diesel_ICE_mass = self.final_SFC_diesel_ICE_mass * energy  # in g
            # in m3
            delta_diesel_ICE_vol = self.final_SFC_diesel_ICE_vol * energy

            emission_delta_CO2 = (
                self.total_factor_CO2 * energy
            )  # Energy consumed per time step delta_t in the                                                                                              #stationary phase # in g
            emission_delta_PM10 = self.total_factor_PM10 * energy  # in g
            emission_delta_NOX = self.total_factor_NOX * energy  # in g
            # in grams
            emissions = {
                "CO2": emission_delta_CO2,
                "PM10": emission_delta_PM10,
                "NOX": emission_delta_NOX,
            }

            edge_geom = shapely.wkt.loads(edge["Wkt"])
            #
            t = datetime.datetime.utcfromtimestamp(timestamp) + datetime.timedelta(
                seconds=total_duration
            )

            energy_profile.append(
                {
                    "e": e,
                    "geometry": edge_geom,
                    "t": t,
                    "duration": duration,
                    "power": power_given,
                    "energy": energy,
                    "fuel": delta_diesel_ICE_vol,
                    "distance": distance,
                    "edge": edge,
                    "upperbound": upperbound,
                    "v": v,
                    **emissions,
                }
            )
            total_distance += distance

        # finished sailing
        # move to destination
        end_node = graph.nodes[path[-1]]
        # TODO: double truth where are we, on the node or on the geometry?
        self.geometry = end_node["geometry"]
        self.node = path[-1]

        # where did we sail? The total sailed path
        if len(path) < 2:
            path_geometry = self.geometry
        else:
            # extrect the geometry
            path_df = dtv_backend.network.network_utilities.path2gdf(path, graph)

            #
            path_geometry = shapely.ops.linemerge(path_df["geometry"].values)
            start_point = graph.nodes[path_df.iloc[0]["start_node"]]["geometry"]
            end_point = graph.nodes[path_df.iloc[-1]["end_node"]]["geometry"]
            first_path_point = shapely.geometry.Point(path_geometry.coords[0])
            # reverse if needed
            start_distance = start_point.distance(first_path_point)
            end_distance = end_point.distance(first_path_point)
            if start_distance > end_distance:
                # invert geometry
                path_geometry = shapely.geometry.LineString(path_geometry.coords[::-1])

        with self.log_context(
            message="Sailing",
            description=f"Sailing ({self.name})",
            ship=self,
            geometry=path_geometry,
            value=total_distance,
            path=path,
            energy_profile=energy_profile,
        ):
            yield self.env.timeout(total_duration)


class Processor(dtv_backend.logbook.HasLog):
    def __init__(self, loading_rate, loading_rate_variation=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loading_rate = loading_rate
        self.loading_rate_variation = loading_rate_variation

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        return self.container.capacity - self.container.level

    def load(
        self,
        source: opentnsim.core.HasContainer,
        destination: opentnsim.core.HasContainer,
        max_load=None,
    ):
        """The loading processes. It takes a ``ship`` and loads it with maximal (max_load)."""
        available = source.container.level
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


Port = type(
    "Port",
    (
        Processor,
        opentnsim.core.Identifiable,
        opentnsim.core.Locatable,
        opentnsim.core.HasResource,
        opentnsim.core.HasContainer,
        opentnsim.core.ExtraMetadata,
    ),
    {},
)


Ship = type(
    "Ship",
    (
        CanWork,
        dtv_backend.berthing.CanBerth,
        opentnsim.core.Identifiable,
        opentnsim.core.HasContainer,
        opentnsim.core.Movable,
        opentnsim.core.Locatable,
        opentnsim.core.VesselProperties,
        opentnsim.energy.ConsumesEnergy,
        opentnsim.core.ExtraMetadata,
    ),
    {},
)
