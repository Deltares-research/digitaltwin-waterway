"""
Run functions for the digital twin waterways
"""
# coding: utf-8

import datetime
import logging

import simpy
import shapely.geometry

# library to load the fairway information network
import dtv_backend.fis

# the simpy processes and objects
import dtv_backend.compat
import dtv_backend.simple
import dtv_backend.network.network_utilities


logger = logging.getLogger(__name__)


def run(config):
    # always start at now
    now = datetime.datetime.now()
    initial_time = now.timestamp()
    env = simpy.Environment(initial_time=initial_time)
    env.epoch = now

    # default no berth
    with_berth = config.get("options", {}).get("with_berth", False)

    # read the network from google for performance reasons
    url = "https://storage.googleapis.com/et-data-science/dtv/network_digital_twin_v0.1.yaml"
    url = "https://zenodo.org/record/4578289/files/network_digital_twin_v0.2.pickle?download=1"
    url = "https://zenodo.org/record/6673604/files/network_digital_twin_v0.3.pickle?download=1"
    G = dtv_backend.fis.load_fis_network(url)
    env.FG = G

    logger.info("Loading ports ⚓")
    ports = []
    for site in config["sites"]:
        port = dtv_backend.simple.Port(env, **site["properties"], **site)
        ports.append(port)

    logger.info("Loading ships 🚢")
    ships = []
    for ship in config["fleet"]:
        kwargs = {}
        kwargs.update(ship)
        kwargs.update(ship["properties"])
        # the ship needs to know about the climate
        if "climate" in config:
            kwargs["climate"] = config["climate"]
        ship = dtv_backend.simple.Ship(env, **kwargs)
        ships.append(ship)

    logger.info("Loadig operator 👩‍💼")
    # Setup and start the simulation
    operator = dtv_backend.simple.Operator(env, ships=ships, **config["operator"])
    # The ships do work for the operator
    for ship in ships:
        env.process(ship.work_for(operator, with_berth=with_berth))
    # The opertor plans the work move everything from A to B
    env.process(operator.plan(ports[0], ports[1]))

    logger.info("Running simulation 👩‍💻")
    # Run for n days
    n_days_in_future = now + datetime.timedelta(days=60)
    env.run(until=n_days_in_future.timestamp())

    return {
        "env": env,
        "operator": operator,
        "ships": ships,
        "config": config,
        "ports": port,
    }


def v2_run(config):
    # always start at now
    now = datetime.datetime.now()
    initial_time = now.timestamp()
    env = simpy.Environment(initial_time=initial_time)
    env.epoch = now

    # default no berth
    with_berth = config.get("options", {}).get("with_berth", False)

    # read the network from google for performance reasons
    url = "https://zenodo.org/record/6673604/files/network_digital_twin_v0.3.pickle?download=1"
    G = dtv_backend.fis.load_fis_network(url)
    env.FG = G

    logger.info("Loading ports ⚓")
    ports = []
    for site in config["sites"]:
        port = dtv_backend.simple.Port(env, **site["properties"], **site)
        ports.append(port)

    logger.info("Loading ships 🚢")
    ships = []
    for ship in config["fleet"]:
        kwargs = {}
        kwargs.update(ship)
        kwargs.update(ship["properties"])
        # the ship needs to know about the climate
        if "climate" in config:
            kwargs["climate"] = config["climate"]
        ship = dtv_backend.simple.Ship(env, **kwargs)
        ships.append(ship)

    logger.info("Loadig operator 👩‍💼")
    # Setup and start the simulation
    operator = dtv_backend.simple.Operator(env, ships=ships, **config["operator"])
    # The ships do work for the operator
    for ship in ships:
        env.process(ship.work_for(operator, with_berth=with_berth))
    # The opertor plans the work move everything from A to B
    env.process(operator.plan(ports[0], ports[1]))

    logger.info("Running simulation 👩‍💻")
    # Run for n days
    n_days_in_future = now + datetime.timedelta(days=60)
    env.run(until=n_days_in_future.timestamp())

    return {
        "env": env,
        "operator": operator,
        "ships": ships,
        "config": config,
        "ports": port,
    }


def create_env(config):

    # always start at now
    now = datetime.datetime.now()
    initial_time = now.timestamp()
    env = simpy.Environment(initial_time=initial_time)
    env.epoch = now

    # read the network from google for performance reasons
    url = "https://zenodo.org/record/6673604/files/network_digital_twin_v0.3.pickle?download=1"
    G = dtv_backend.fis.load_fis_network(url)
    env.FG = G
    return env


def create_ports(env, config):
    # ports
    logger.info("Loading ports ⚓")
    ports = []
    for site in config["sites"]:
        # port = dtv_backend.simple.Port(env, **site["properties"], **site)
        node = site["properties"]["n"]
        loading_rate = site["properties"]["loadingRate"]
        loading_rate_variation = site["properties"]["loadingRateVariation"]
        port = dtv_backend.compat.Port(
            env=env,
            node=node,
            loading_rate=loading_rate,
            loading_rate_variation=loading_rate_variation,
            **site["properties"],
            **site
        )
        ports.append(port)
    return ports


def create_ships(env, config):
    """create ships"""
    logger.info("Loading ships 🚢")
    ships = []
    for ship in config["fleet"]:
        kwargs = {}
        kwargs.update(ship)
        kwargs.update(ship["properties"])
        kwargs["v"] = 3
        route = [feature["properties"]["n"] for feature in config["route"]]
        kwargs["route"] = route
        geometry = shapely.geometry.shape(ship["geometry"])
        node, dist = dtv_backend.fis.find_closest_node(env.FG, geometry)
        kwargs["node"] = node
        # the ship needs to know about the climate
        if "climate" in config:
            kwargs["climate"] = config["climate"]
        # ship = dtv_backend.simple.Ship(env, **kwargs)
        ship = dtv_backend.compat.Ship(env=env, **kwargs)
        ships.append(ship)
    return ships


def create_operator(env, ships, ports, config):
    """create an operator"""
    logger.info("Loadig operator 👩‍💼")

    # default no berth
    with_berth = config.get("options", {}).get("with_berth", False)

    # Setup and start the simulation
    operator = dtv_backend.simple.Operator(env=env, ships=ships, **config["operator"])
    # The ships do work for the operator
    for ship in ships:
        env.process(ship.work_for(operator, with_berth=with_berth))
    # The opertor plans the work move everything from A to B
    env.process(operator.plan(ports[0], ports[1]))
    return operator


def v3_run(config):
    """run a simulation using the opentnsim compatibility kernel"""
    logger.info("Running simulation 👩‍💻")
    # Run for n days

    env = create_env(config)
    ports = create_ports(env, config)
    ships = create_ships(env, config)
    operator = create_operator(env, ships, ports, config)

    n_days = 60
    n_days_in_future = env.epoch + datetime.timedelta(days=n_days)
    env.run(until=n_days_in_future.timestamp())
    result = {
        "env": env,
        "operator": operator,
        "ships": ships,
        "config": config,
        "ports": ports,
    }

    return result
