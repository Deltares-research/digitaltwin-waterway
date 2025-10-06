# package(s) related to time, space and id
import argparse
import datetime
import functools
import io
import json
import pathlib
import pickle
import time

# dtv_backend
import dtv_backend.fis as fis
import geopandas as gpd
import movingpandas as mpd

# Used for making the graph to visualize our problem
import networkx as nx

# Used for mathematical functions
import numpy as np

# OpenTNSIM
import opentnsim
import opentnsim.core as core
import opentnsim.graph_module as graph_module

# package(s) for data handling
import pandas as pd
import requests

# you need these dependencies (you can get these from anaconda)
# package(s) related to the simulation
import simpy
from dtv_backend.lock import Lock, Locks
from networkx.exception import NetworkXNoPath

# spatial libraries
from shapely.geometry import Point
from tqdm import tqdm
from tqdm.auto import tqdm

afzetting_bool = True
afzetting_node_1 = "8863326"
afzetting_node_2 = "30984545"

output_dir = pathlib.Path().resolve() / "output"
dir_graphs = output_dir / "graphs"
dir_graphs.mkdir(exist_ok=True, parents=True)

cemt_classes_ordered = {
    "0": 0,
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "IVa": 5,
    "Va": 6,
    "Vb": 7,
    "VIa": 8,
    "VIb": 9,
    "VIc": 10,
    "VIIa": 11,
}
# define synonyms:
code_synonyms = {
    "_0": "0",
    "V_A": "Va",
    "V_B": "Vb",
    "VI_A": "VIa",
    "VI_B": "VIb",
    "VI_C": "VIc",
}


def create_graph(
    dir_graphs,
    code_synonyms,
    afzetting_node_1=None,
    afzetting_node_2=None,
):
    dir_graphs.mkdir(exist_ok=True, parents=True)

    # Load graph
    url = "https://zenodo.org/record/6673604/files/network_digital_twin_v0.3.pickle?download=1"
    graph1 = fis.load_fis_network(url).copy()

    # remove edge
    graph1.remove_edge(afzetting_node_1, afzetting_node_2)

    graph = graph_module.Graph()
    graph.graph = graph1
    graph.graph_info = opentnsim.utils.info(graph.graph)

    # save afzetting in geopandas
    afzetting = pd.DataFrame(
        {"A": graph1.nodes[afzetting_node_1], "B": graph1.nodes[afzetting_node_2]}
    ).T
    afzetting = gpd.GeoDataFrame(afzetting, crs="EPSG:4326")
    afzetting.to_file(dir_graphs / "afzetting_locatie")

    # save graph
    edgelist = gpd.GeoDataFrame(nx.to_pandas_edgelist(graph.graph))
    edgelist.to_file(dir_graphs / f"graph_afzetting")

    for edge in graph.graph.edges:
        # replace synonyms
        if graph.graph.edges[edge]["Code"] in code_synonyms:
            graph.graph.edges[edge]["Code"] = code_synonyms[
                graph.graph.edges[edge]["Code"]
            ]

    return graph


def load_ivs_data(ivs_path):
    data = gpd.read_file(ivs_path)
    data.reset_index(drop=False, inplace=True, names="name")

    # #filter data op bestaande iso datum en geometry.
    data["datetime"] = pd.to_datetime(
        data["v05_06_begindt_evenement_iso"], format="ISO8601", errors="coerce"
    )
    data.dropna(subset=["datetime", "geometry"], inplace=True)

    t_begin = pd.Timestamp("2023-10-10", tz="UTC")
    t_end = pd.Timestamp("2023-10-12", tz="UTC")

    condition_1 = data.datetime >= (t_begin)
    condition_2 = data.datetime < (t_end)
    condition_3 = data.UNLO_bestemming != data.UNLO_herkomst
    condition_6 = ~data.SK_CODE.isna()

    idx = np.logical_and.reduce(
        [
            condition_1,
            condition_2,
            condition_3,
            condition_6,
        ]
    )
    data = data[idx]
    return data


def change_ship_types(gdf, cemt_path):
    # rename column SK
    gdf["SK_CODE"] = gdf["SK_CODE"].rename(
        {
            "C3l": "C3L",
            "C2l": "C2L",
            "B04": "BO4",
            "B03": "BO3",
            "B02": "BO2",
            "B01": "BO1",
        }
    )

    # add cmt classe
    database_rws_cemt = pd.read_json(cemt_path)
    dict_rws_cemt = dict(
        zip(database_rws_cemt["RWS-class"], database_rws_cemt["CEMT-class"])
    )
    gdf["CEMT"] = gdf["SK_CODE"].map(dict_rws_cemt)

    gdf["length"] = gdf["SK_CODE"].map(fis.rws_klasse_to_shiplength)
    gdf["width"] = gdf["SK_CODE"].map(fis.rws_klasse_to_shipwidth)

    return gdf


# define speed:
def compute_v_provider(v_empty, v_full):
    return lambda x: 1


def create_vessels(gdf, graph, output_dir):

    # Make a class out of mix-ins
    TransportResource = type(
        "TransportResource",
        (
            core.Identifiable,
            core.ContainerDependentMovable,
            core.HasResource,
            core.Routable,
            core.VesselProperties,
            core.ExtraMetadata,
        ),
        {},
    )

    saved_routes = {}
    # create vessels
    vessels = []
    failed_vessels = []
    for index, row in tqdm(gdf.iterrows()):
        # determine path
        try:
            if str(row.name) in saved_routes.keys():
                path = saved_routes[str(row.name)]
            else:
                point_1 = fis.find_closest_node(
                    graph.graph, Point(row.geometry.coords[0])
                )
                point_2 = fis.find_closest_node(
                    graph.graph, Point(row.geometry.coords[-1])
                )
                path = fis.path_restricted_to_cemt_class(
                    graph=graph.graph,
                    origin=point_1[0],
                    destination=point_2[0],
                    ship_cemt_classe=f"{row['CEMT']}",
                    ordered_cemt_classes=cemt_classes_ordered,
                )
            # path = nx.dijkstra_path(graph.graph, point_1[0], point_2[0], weight=compute_weight)
            # determine capacity
            capacity = max(row.v18_Laadvermogen * 1000, row.v38_Vervoerd_gewicht, 1)
            data_vessel = {
                "env": None,
                "name": row.name,
                "type": row["v15_1_Scheepstype_RWS"],
                "B": row["width"],
                "L": row["length"],
                "route": path,
                "geometry": Point(row.geometry.coords[0]),  # lon, lat
                "capacity": capacity,
                "v": 0.5144 * 8,  # 8 knopen
                "compute_v": compute_v_provider(v_empty=0.5144 * 8, v_full=0.5144 * 8),
                "departure_time": pd.to_datetime(row["v05_06_begindt_evenement_iso"]),
            }
            vessel = TransportResource(**data_vessel)
            vessels.append(vessel)
        except NetworkXNoPath:
            failed_vessels.append(row.name)
        except ValueError:
            failed_vessels.append(row.name)
    print(f"Failed vessels: {failed_vessels}")
    print(f"Number of vessels: {len(vessels)}")

    # path_vessel_routes = output_dir / f"vessel_routes_afzetting_{afzetting_bool}.json"
    a = {vessel.name: vessel.route for vessel in vessels}

    json.dump(a, open(output_dir / f"vessel_routes_afzetting.json", "w"))
    json.dump(
        failed_vessels,
        open(output_dir / f"failed_vessels_afzetting.json", "w"),
    )
    return a


# define speed:
def compute_v_provider(v_empty, v_full):
    return lambda x: 1


# json.dump(a, open(path_vessel_routes, 'w'))
# json.dump(failed_vessels, open(output_dir / f'failed_vessels_afzetting_{afzetting_bool}.json', 'w'))


def start(env, vessel):
    while True:
        # wait untill ship will start sailing
        time_departure = time.mktime(vessel.metadata["departure_time"].timetuple())
        if env.now > time_departure:
            # print(f"Vessel {vessel.name} is starting at {time_departure} \n {vessel.metadata['departure_time']} \n current time: {env.now}")
            pass
            # print(i)
            # print(time_departure-env.now)
        yield env.timeout(max(0, time_departure - env.now))

        # start sailing
        vessel.log_entry_v0("Start sailing", env.now, "", vessel.geometry)
        if vessel.name == 100134:
            print(f"env.now: {env.now}, departure_time: {time_departure}")
        if vessel.name == 100134:
            print("Before move", env.now, vessel.name, vessel.v, vessel.route)
        yield from vessel.move()
        if vessel.name == 100134:
            print("After move", env.now, vessel.name, vessel.v)

        if vessel.name == 100134:
            print(vessel.name, vessel.geometry)
        vessel.log_entry_v0("Stop sailing", env.now, "", vessel.geometry)

        if (
            vessel.geometry
            == nx.get_node_attributes(env.FG, "geometry")[vessel.route[-1]]
        ):
            break


def run_simulation(vessels, graph, locks_dir):
    # Start simpy environment
    simulation_start = min([vessel.metadata["departure_time"] for vessel in vessels])

    env = simpy.Environment(initial_time=time.mktime(simulation_start.timetuple()))
    env.epoch = time.mktime(simulation_start.timetuple())

    env.FG = graph.graph

    # create schuttijden dict
    schuttijden = pd.read_csv(
        locks_dir / "passeertijden.csv", index_col=[1, 2], header=0
    )["mean"]
    schuttijden = schuttijden.rename(
        {
            "Sluis 13": "sluis 13",
            "Sluis Amerongen": "sluis Amerongen",
            "Sluis Maasbracht": "sluis Maasbracht",
            "Sluis Schijndel": "sluis Schijndel",
            "Sluis St. Andries": "sluis St. Andries",
        }
    )
    schuttijden_dict = {}
    for sluis, sluiskolk in schuttijden.index:
        if sluis not in schuttijden_dict:
            schuttijden_dict[sluis] = {}
        schuttijden_dict[sluis][sluiskolk] = schuttijden[(sluis, sluiskolk)]

    # create locks
    locks = Locks(env=env, schuttijden=schuttijden_dict)

    for i, vessel in enumerate(vessels):
        # Add environment and path to the vessel
        vessel.env = env

        # add passing of a lock
        filled_pass_lock = functools.partial(locks.pass_lock, vessel=vessel)
        vessel.on_pass_edge_functions = [filled_pass_lock]

        # Add the movements of the vessel to the simulation
        env.process(start(env, vessel))

    env.run(until=pd.Timestamp("2023-10-14 00:00:00", tz="UTC").timestamp())

    return vessels, locks


def save_vessel_log(vessels, log_dir: pathlib.Path):
    log_dir.mkdir(exist_ok=True)
    # save the logs and trajectories of vessels
    plot_dir = output_dir / "plots_routes"
    plot_dir.mkdir(exist_ok=True)

    log = gpd.GeoDataFrame()
    for vessel in vessels:
        if len(vessel.logbook) == 0:
            continue
        vessel_log = gpd.GeoDataFrame(
            vessel.logbook, geometry="Geometry", crs="EPSG:4326"
        )
        vessel_log["trajectory_id"] = f"vessel_{vessel.name}_trip_1"
        vessel_log["object_id"] = f"vessel_{vessel.name}"
        log = pd.concat([log, vessel_log])
    mpd_log = mpd.TrajectoryCollection(
        log,
        traj_id_col="trajectory_id",
        obj_id_col="object_id",
        t="Timestamp",
    )
    mpd_log.to_line_gdf().to_file(
        log_dir / f"trajectories_afzetting_{afzetting_bool}.gpkg"
    )


def save_locks_log(locks, log_dir: pathlib.Path):
    log_dir.mkdir(exist_ok=True)
    # Save the logs of the locks
    lock_dfs = []
    for id, lock_object in locks.locks_resources.items():
        logbook = pd.DataFrame(lock_object.logbook)
        for chamber in lock_object.chambers:
            logbook_chamber = pd.DataFrame(chamber.logbook)
            logbook = pd.concat([logbook, logbook_chamber], axis=0)
        if len(logbook) == 0:
            continue
        logbook = logbook.sort_values(by="Timestamp").reset_index(drop=True)
        lock_properties = pd.DataFrame(logbook["Value"].values.tolist())
        lock_df = pd.concat([logbook, lock_properties], axis=1)
        lock_df["lock_id"] = id
        lock_dfs.append(lock_df)

    all_locks_df = pd.concat(lock_dfs, axis=0)
    all_locks_df = all_locks_df.drop(columns=["Value"])
    all_locks_df.to_csv(log_dir / f"locks_afzetting_{afzetting_bool}.csv")


def main():
    parser = argparse.ArgumentParser(description="Test ship route simulator")
    parser.add_argument(
        "--remove_source", type=str, required=True, help="Source node to remove"
    )
    parser.add_argument(
        "--remove_target", type=str, required=True, help="Target node to remove"
    )
    args = parser.parse_args()

    source = args.remove_source
    target = args.remove_target

    code_synonyms = {
        "_0": "0",
        "V_A": "Va",
        "V_B": "Vb",
        "VI_A": "VIa",
        "VI_B": "VIb",
        "VI_C": "VIc",
    }
    input_dir = pathlib.Path(__file__).parent.parent / "input"
    output_dir = (
        pathlib.Path(__file__).parent.parent
        / f"output/simulations/{source}_to_{target}"
    )
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"=== SIMULATION START ===")
    print(f"Removing edge: {source} -> {target}")
    graph = create_graph(
        dir_graphs=output_dir / "graphs",
        code_synonyms=code_synonyms,
        afzetting_node_1=source,
        afzetting_node_2=target,
    )

    print(f"Loading IVS data")
    ivs_gdf = load_ivs_data(ivs_path=input_dir / "ivs/ivs-2024-geocoded.gpkg")
    print(f"Filtering IVS data")
    ivs_gdf = change_ship_types(
        gdf=ivs_gdf, cemt_path=input_dir / "DTV_shiptypes_database.json"
    )

    print(f"Creating vessels")
    vessels = create_vessels(gdf=ivs_gdf, graph=graph, output_dir=output_dir)

    print(f"=== RUNNING SIMULATION ===")
    vessels, locks = run_simulation(
        vessels=vessels,
        graph=graph,
        locks_dir=input_dir / "passeertijden/passeertijden.csv",
    )

    save_vessel_log(vessels=vessels, log_dir=output_dir / "logs")
    save_locks_log(locks=locks, log_dir=output_dir / "logs")

    print(f"Result saved to {output_dir}")
    print(f"=== SIMULATION END ===")


if __name__ == "__main__":
    main()
