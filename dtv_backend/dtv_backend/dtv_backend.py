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
    
    # create a temporary file
    f = tempfile.NamedTemporaryFile()
    f.close()
    
    # retrieve the info and create the graph
    urllib.request.urlretrieve(url, f.name)
    G = nx.read_yaml(f.name)
    
    # the temp file can be deleted
    del f
    
    # making geometry really a geometry type
    for n in G.nodes:
        G.nodes[n]['geometry'] = shapely.geometry.Point(G.nodes[n]['X'], G.nodes[n]['Y'])
    
    # add graph to environment (make sure the network is added as env.FG as to fit with openTNSim)
    env.FG = G.copy()
    
    # provide info
    click.echo("Network succesfully added to simulation")






