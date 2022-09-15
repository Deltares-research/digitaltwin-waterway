#!/usr/bin/env python3
import opentnsim.core
import shapely.geometry
from pint import UnitRegistry

import opentnsim.core
import opentnsim.energy

import dtv_backend.berthing


ureg = UnitRegistry()


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

    @property
    def max_load(self):
        """return the maximum cargo to load"""
        return self.container.capacity - self.container.level

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

        # TODO: should not use the path from the config
        # TODO: check if we're using this move or the movable move
        # TODO: add energy consumption calculation per on_pass_edge
        # TODO: log energy consumption

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
                path = dtv_backend.fis.shorted_path(graph, self.node, destination.node)
            elif isinstance(destination, str):
                path = dtv_backend.fis.shorted_path(graph, self.node, destination)
            else:
                raise ValueError(
                    f"destination has no node and is not a string: {destination}"
                )
        if not path:
            raise ValueError("no path found")

        total_distance = 0
        for edge in zip(path[:-1], path[1:]):
            distance = graph.edges[edge]["length_m"]
            total_distance += distance

        # move to destination
        end_node = graph.nodes[path[-1]]
        self.geometry = end_node["geometry"]

        if len(path) < 2:
            path_geometry = self.geometry
        else:
            # extrect the geometry
            path_df = dtv_backend.network.network_utilities.path2gdf(path, graph)

            # convert to single linestring
            path_geometry = shapely.ops.linemerge(path_df["geometry"].values)

            # TODO: Check which way we are sailing? Is that what wer do here.
            start_point = graph.nodes[path_df.iloc[0]["start_node"]]["geometry"]
            end_point = graph.nodes[path_df.iloc[-1]["end_node"]]["geometry"]
            first_path_point = shapely.geometry.Point(path_geometry.coords[0])
            start_distance = start_point.distance(first_path_point)
            end_distance = end_point.distance(first_path_point)
            if start_distance > end_distance:
                # invert geometry
                path_geometry = shapely.geometry.LineString(path_geometry.coords[::-1])

        # Aftter sailing log the following energy_consumption in a table format:
        # [
        #   {edge: [0, 1], duration: 180s, distance: 100, energy: 10kWh, co2: 10, nox: 10}
        # ]
        # {"total_distance": 1231, "energy_table": [{}, {}, {...}]}

        with self.log_context(
            message="Sailing",
            description=f"Sailing ({self.name})",
            ship=self,
            geometry=path_geometry,
            value=total_distance,
            path=path,
        ):
            yield self.env.timeout(total_distance / self.v)


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
        opentnsim.energy.ConsumesEnergy,
        opentnsim.core.Identifiable,
        opentnsim.core.HasContainer,
        opentnsim.core.Movable,
        opentnsim.core.Locatable,
        opentnsim.core.ExtraMetadata,
    ),
    {},
)
