"""Console script for dtv_backend."""
import sys
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
    click.echo("Running a simulation")
    # read input file
    # load network
    # create vessels
    # create sites
    # creat scenarios
    # run
    # postprocess
    # cleanup
    pass



if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
