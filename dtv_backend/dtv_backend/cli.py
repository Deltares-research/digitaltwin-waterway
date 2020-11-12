"""Console script for dtv_backend."""
import sys
import json

import click


@click.group()
def main(args=None):
    """Console script for dtv_backend."""
    click.echo("Starting dtv_backend")
    # pre load the network
    return 0

@main.command()
@click.argument('input', type=click.File('r'))
def simulate(input):
    """run a simulation"""
    # click.echo("Running a simulation")
    # config = json.load(input)

    # config["vessels"]
    # config["sites"]
    # config["activites"]
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
    pass



if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
