# coding: utf-8

"""Console script for dtv_backend."""
import sys
import json
import logging
import copy
import datetime

import click
import pandas as pd

# dependencies
import dtv_backend.network.network_utilities
import dtv_backend.simple
import dtv_backend.simulate
import dtv_backend.postprocessing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@click.group()
def main(args=None):
    """Console script for dtv_backend."""
    logger.info("Starting Digital Twin Vaarwegen 👥")
    return 0


@main.command()
@click.argument('input', type=click.File('r'))
def simulate(input):
    """run a simulation"""

    # click.echo("Running a simulation")
    config = json.load(input)

    logger.info(f"Loading configuration file ⚙")

    # set up an environment
    result = dtv_backend.simulate.run(input.name)

    logger.info("Writing logbook     ")
    log_df = pd.DataFrame(result["operator"].logbook)
    log_df.to_csv('logbook.csv')
    logger.info("Writing charts 📊")
    fig = dtv_backend.postprocessing.log2gantt(log_df)
    fig.write_image('gantt.svg')


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
