# coding: utf-8

import datetime
import logging
import geojson
import simpy
import time

# library to load the fairway information network
import dtv_backend.fis
# the simpy processes and objects
import dtv_backend.simple
import dtv_backend.network.network_utilities


logger = logging.getLogger(__name__)

def run(input_path):

    # read input file
    with open(input_path) as f:
        config = geojson.load(f)


    # always start at now
    now = datetime.datetime.now()
    initial_time = now.timestamp()
    env = simpy.Environment(initial_time=initial_time)
    env.epoch = now

    # read the network from google for performance reasons
    url = 'https://storage.googleapis.com/et-data-science/dtv/network_digital_twin_v0.1.yaml'
    G = dtv_backend.fis.load_fis_network(url)
    env.FG = G

    logger.info("Loading ports ⚓")
    ports = []
    for site in config['sites']:
        port = dtv_backend.simple.Port(env, **site['properties'], **site)
        ports.append(port)


    logger.info("Loading ships 🚢")
    ships = []
    for ship in config['fleet']:
        kwargs = {}
        kwargs.update(ship)
        kwargs.update(ship['properties'])
        # the ship needs to know about the climate
        if 'climate' in config:
            kwargs['climate'] = config['climate']
        ship = dtv_backend.simple.Ship(env, **kwargs)
        ships.append(ship)



    logger.info("Loadig operator 👩‍💼")
    # Setup and start the simulation
    operator = dtv_backend.simple.Operator(env, ships=ships, **config['operator'])
    # The ships do work for the operator
    for ship in ships:
        env.process(ship.work_for(operator))
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
        "ports": port
    }
