"""
Console script for dtv_backend.
"""
import sys
import json
import logging
import copy
import datetime

import click
import geojson
import pandas as pd
# add Flask CLI
from flask.cli import FlaskGroup

# dependencies
import dtv_backend.network.network_utilities
import dtv_backend.simple
import dtv_backend.simulate
import dtv_backend.postprocessing
import dtv_backend.server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group(cls=FlaskGroup, create_app=dtv_backend.server.create_app)
def main():
    """server"""
    logger.info("Starting Digital Twin Vaarwegen 👥")



@main.command()
@click.argument('input', type=click.File('r'))
def simulate(input):
    """run a simulation"""

    logger.info("Loading configuration file ⚙")
    # read input file
    with open(input.name) as f:
        config = geojson.load(f)

    # set up an environment
    result = dtv_backend.simulate.run(config)

    logger.info("Writing logbook     ")
    log_df = pd.DataFrame(result["operator"].logbook)
    log_df.to_csv('logbook.csv')
    logger.info("Writing charts 📊")
    fig = dtv_backend.postprocessing.log2gantt(log_df)
    fig.write_image('gantt.svg')


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
