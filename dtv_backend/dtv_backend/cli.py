"""Console script for dtv_backend."""
import sys
import json
import logging
import copy
import datetime

import click

# dependencies
import dtv_backend.core.sites
import dtv_backend.core.vessels
from dtv_backend.processes.single_run_process_fleet import single_run_process_fleet


import dtv_backend.dtv_backend as backend
import dtv_backend.network.network_utilities

@click.group()
def main(args=None):
    """Console script for dtv_backend."""

    logging.basicConfig(level=logging.INFO)
    click.echo("Starting dtv_backend")


    return 0

@main.command()
@click.argument('input', type=click.File('r'))
def simulate(input):
    """run a simulation"""

    # click.echo("Running a simulation")
    config = json.load(input)

    click.echo(f"loaded {list(config.keys())}")

    # set up an environment
    env = backend.provide_environment()

    # pre load the network
    backend.load_DTV_network_to_env(env)

    sites = [
        dtv_backend.core.sites.feature2site(site, env)
        for site
        in config['sites']
    ]

    cranes = []
    for site_feature in config['sites']:
        crane_feature = copy.deepcopy(site_feature)

        crane_feature['properties']['name'] = 'Crane ' + crane_feature['properties']['name']
        crane = dtv_backend.core.sites.feature2site(crane_feature, env)
        cranes.append(crane)

    origin = sites[0]
    destination = sites[1]

    crane_origin = cranes[0]
    crane_destination = cranes[1]

    lobith_discharge = config["climate"]["lobith"]

    max_draught = dtv_backend.network.network_utilities.determine_max_draught_on_path(
        env.FG,
        origin,
        destination,
        lobith_discharge
    )
    click.echo(f"max draught: {max_draught}")

    vessels = [
        dtv_backend.core.vessels.feature2vessel(feature, env)
        for feature
        in config['fleet']
    ]

    single_run_process_fleet(
        vessels,
        env,
        origin,
        destination,
        loader=crane_origin,
        unloader=crane_destination
    )
    click.echo(f'Simulation starting @ {datetime.datetime.utcfromtimestamp(env.now)}')
    env.run()
    click.echo(f'Simulation finished @ {datetime.datetime.utcfromtimestamp(env.now)}')
    import pandas as pd
    print(pd.DataFrame(crane_origin.log))

    # activity = config["activities"][0]
    # activity["source"]
    # activity["destination"]
    # activity["vessel"]
    # site = config["sites"][0]
    # # geojson like format
    # site["properties"]["load"]
    # site["id"]
    # site["geometry"]
    # site["environment"]
    # site["environment"]["discharge"]["lobith"] = 3.0
    # simulation = load_simulation(config)
    # convert vessel config into types

    # load network


    # convert config["sites"] into openCLSim site
    # create activities from sites and loads

    # set maximum waterlevel in network based on environment

    # determine path, based on vessel and source/destination and network
    # determine maximum load based on path and load/depth function from vessel
    #

    # load activities as process into environment

    # run

    # postprocess

    # extract log -> dataframe
    # data frame interpolate to time (movingpandas)
    # generate visualisations -> qgis, kml, movies
    #
    # cleanup

    # # define origin
    # # TODO: specify the correct inputs from the config
    # origin = backendSites.provideSite(env = main.env,
    #                        point = config.origin.point,
    #                        name = config.origin.name,
    #                        level = config.origin.level,
    #                        loading_rate = config.origin.loading_rate,
    #                        unloading_rate = config.origin.unloading_rate)

    # # define destination
    # # TODO: specify the correct inputs from the config
    # destination = backendSites.provideSite(env = main.env,
    #                        point = config.destination.point,
    #                        name = config.destination.name,
    #                        level = config.destination.level,
    #                        loading_rate = config.destination.loading_rate,
    #                        unloading_rate = config.destination.unloading_rate)

    # # add the vessels to the simulation as a fleet
    # # TODO: specify the correct inputs from the config within this function
    # fleet = backend.add_fleet_to_simulation(main.env, origin, config)

    # # perform transport task
    # single_run_process_fleet(fleet, main.env, origin, destination, loader=origin, unloader=destination)


    # pass



if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
