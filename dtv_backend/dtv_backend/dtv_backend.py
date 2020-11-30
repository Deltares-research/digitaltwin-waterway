"""Main module."""

# dependencies
import simpy
import datetime
import time
import tempfile
import urllib
import networkx as nx
import shapely.geometry
import click

# our software
import opentnsim.core as TNcore
import openclsim.model as CLmodel
import openclsim.core as CLcore

from dtv_backend.core import vessels as backendVessels
from dtv_backend.network.network import load_fis_network

#%% Provide environment
def provide_environment(simulation_start=None):
    """
    Function that provides a simpy environment with the desired startdate

    Parameters
    ----------
    simulation_start : datetime.datetime or datetime.date object
        The desired startdate of the simulation.

    Returns
    -------
    env : simpy.environment
        The 'empty' simpy environment.

    """
    # provide info
    click.echo("Defining simulation environment")

    # set the starting time
    if simulation_start is None:
        simulation_start = datetime.date.today()
    else:
        # assert the correct format
        assert (isinstance(simulation_start, datetime.datetime) \
                or isinstance(simulation_start, datetime.date)), \
            'The simulation starttime must be either a "datetime.date" or "datetime.datetime" object'

    # define the environment
    env = simpy.Environment(initial_time = time.mktime(simulation_start.timetuple()))
    env.epoch = time.mktime(simulation_start.timetuple())

    return env


#%% Network functions
def load_DTV_network_to_env(env):
    """
    Loads DigiTwin network to a graph which is added to a
    simpy environment as env.network

    Parameters
    ----------
    env : simpy.enviromnent
        The simpy environment to which the .

    Returns
    -------
    None.

    """
    # provide info
    click.echo("Starting (down)loading the network")
    # link to the latets version of the network
    url = 'https://zenodo.org/record/3981105/files/network_digital_twin_v0.1.yaml'
    # alternative url (zenodo was unavailable today)
    url = 'https://storage.googleapis.com/et-data-science/dtv/network_digital_twin_v0.1.yaml'

    G = load_fis_network(url)

    # add graph to environment (note that it is added as attribute FG as to ensure with the defailt in openTNSim)
    env.FG = G.copy()

    # provide info
    click.echo("Network succesfully added to simulation")


#%%
def add_fleet_to_simulation(env, origin, config):
    """
    Adds the fleet to the environment based on the input

    Parameters
    ----------
    env : simpy environment
        .
    origin : a DTV site
        the starting point of the fleet.
    input : TYPE
        the input file.

    Returns
    -------
    fleet : list of vessels
        .

    """
    # TODO: decode the input to extract the vessels
    # define empty fleet
    fleet = []

    # loop actoss the info in the input to add the individual vessels to the fleet
    for vessel_info in config.vessels:
        # TODO: extract all the relevant info of these vessels from the input and add do dict
        data_vessel = {
                        "env": env,
                        "name": vessel_info.name,
                        "geometry": origin.geometry,
                        "loading_rate": 1,
                        "unloading_rate": 1,
                        "capacity": vessel_info.capacity,
                        "route": None,
                        'vessel_type': vessel_info.type,
                        'installed_power': 1000,
                        'width': vessel_info.width,
                        'length': vessel_info.length,
                        'height_empty': vessel_info.height_empty,
                        'height_full': vessel_info.height_full,
                        'draught_empty': vessel_info.draught_empty,
                        'draught_full': vessel_info.draught_full
                    }

        fleet.append(backendVessels.provideVessel(**data_vessel))

    return fleet


#%%



#%% test with openCLSim and openTNSim

# TODO: fix this, this ofcourse does not work
#from CLmodel.move_activity import MoveActivity
#from CLmodel.sequential_activity import SequentialActivity
#from CLmodel.shift_amount_activity import ShiftAmountActivity
#from CLmodel.while_activity import WhileActivity


# def single_run_process(
#     env,
#     registry,
#     name,
#     origin,
#     destination,
#     mover,
#     loader,
#     unloader,
#     start_event=None,
#     stop_event=[],
#     requested_resources={},
#     postpone_start=False,
# ):
#     """Single run activity for the simulation."""
#     if stop_event == []:
#         stop_event = [
#             {
#                 "or": [
#                     {"type": "container", "concept": origin, "state": "empty"},
#                     {"type": "container", "concept": destination, "state": "full"},
#                 ]
#             }
#         ]

#     # single run means that we move to origin, load, move to destination, unload
#     single_run = [
#         MoveActivity(
#             env=env,
#             registry=registry,
#             requested_resources=requested_resources,
#             postpone_start=True,
#             name=f"{name} sailing empty",
#             mover=mover,
#             destination=origin,
#         ),
#         ShiftAmountActivity(
#             env=env,
#             registry=registry,
#             requested_resources=requested_resources,
#             postpone_start=True,
#             phase="loading",
#             name=f"{name} loading",
#             processor=loader,
#             origin=origin,
#             destination=mover,
#         ),
#         MoveActivity(
#             env=env,
#             registry=registry,
#             requested_resources=requested_resources,
#             postpone_start=True,
#             name=f"{name} sailing filled",
#             mover=mover,
#             destination=destination,
#         ),
#         ShiftAmountActivity(
#             env=env,
#             registry=registry,
#             requested_resources=requested_resources,
#             phase="unloading",
#             name=f"{name} unloading",
#             postpone_start=True,
#             processor=unloader,
#             origin=mover,
#             destination=destination,
#         ),
#     ]

#     #
#     activity = SequentialActivity(
#         env=env,
#         name=f"{name} sequence",
#         registry=registry,
#         sub_processes=single_run,
#         postpone_start=True,
#     )

#     #
#     while_activity = WhileActivity(
#         env=env,
#         name=name,
#         registry=registry,
#         sub_process=activity,
#         condition_event=stop_event,
#         start_event=start_event,
#         postpone_start=postpone_start,
#     )

#     return single_run, activity, while_activity
