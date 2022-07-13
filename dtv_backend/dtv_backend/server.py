import pathlib
import logging

import flask
import pandas as pd
import datetime

import dtv_backend.simulate
import dtv_backend.postprocessing
import dtv_backend.fis
import dtv_backend.climate
import geopandas as gpd

import networkx as nx

from flask_cors import CORS


logger = logging.getLogger(__name__)
dtv = flask.Blueprint("dtv", __name__)

# TODO: add swaggerui_blueprint
url = "https://zenodo.org/record/4578289/files/network_digital_twin_v0.2.pickle?download=1"
url = "https://zenodo.org/record/6673604/files/network_digital_twin_v0.3.pickle?download=1"


@dtv.route("/")
def home():
    return {"message": "Welcome to the Digital Twin Fairways"}


@dtv.route("/simulate", methods=["POST"])
def simulate():
    config = flask.request.json
    result = dtv_backend.simulate.run(config)
    log_df = pd.DataFrame(result["operator"].logbook)
    log_json = dtv_backend.postprocessing.log2json(log_df)
    env = result["env"]
    result = {
        "log": log_json,
        "config": config,
        "env": {
            "epoch": env.epoch.timestamp(),
            "epoch_iso": env.epoch.isoformat(),
            "now": env.now,
            "now_iso": datetime.datetime.fromtimestamp(env.now).isoformat(),
        },
    }
    return flask.jsonify(result)


@dtv.route("/v2/simulate", methods=["POST"])
def v2_simulate():
    config = flask.request.json
    # update to new run method
    result = dtv_backend.simulate.v2_run(config)
    log_df = pd.DataFrame(result["operator"].logbook)
    log_json = dtv_backend.postprocessing.log2json(log_df)
    env = result["env"]
    result = {
        "log": log_json,
        "config": config,
        "env": {
            "epoch": env.epoch.timestamp(),
            "epoch_iso": env.epoch.isoformat(),
            "now": env.now,
            "now_iso": datetime.datetime.fromtimestamp(env.now).isoformat(),
        },
    }
    return flask.jsonify(result)


@dtv.route("/v3/simulate", methods=["POST"])
def v3_simulate():
    """generate response for a simulation with the opentnsim compatible kernel"""
    config = flask.request.json
    result = dtv_backend.simulate.v3_run(config)

    env = result["env"]
    log_df = pd.DataFrame(result["operator"].logbook)
    log_json = dtv_backend.postprocessing.log2json(log_df)

    response = {
        "log": log_json,
        "config": config,
        "env": {
            "epoch": env.epoch.timestamp(),
            "epoch_iso": env.epoch.isoformat(),
            "now": env.epoch,
            "now_iso": datetime.datetime.fromtimestamp(env.now).isoformat(),
        },
    }
    return response


@dtv.route("/find_route", methods=["POST"])
def find_route():
    """return a the route that passes through the `{"waypoints": ["node", "node"]}`"""
    body = flask.request.json
    waypoints = body["waypoints"]
    network = dtv_backend.fis.load_fis_network(url)

    route = dtv_backend.fis.get_route(waypoints, network)
    return route


@dtv.route("/ships", methods=["GET"])
def ships():
    """return a the list of ships"""
    ships = pd.read_json(
        dtv_backend.get_src_path() / "data" / "DTV_shiptypes_database.json"
    )
    ships = ships[ships.Included.astype("bool")]
    result = ships.to_dict(orient="records")
    return result


@dtv.route("/waterlevels", methods=["POST"])
def waterlevels():
    body = flask.request.json
    climate = body["climate"]
    network = dtv_backend.fis.load_fis_network(url)

    river_with_discharges_gdf = dtv_backend.climate.get_river_with_discharges_gdf()
    river_interpolator_gdf = dtv_backend.climate.create_river_interpolator_gdf(
        river_with_discharges_gdf
    )

    epsg_utm31n = 32631

    # compute in utm zone
    result = dtv_backend.climate.interpolated_values_for_climate(
        climate=climate,
        graph=network,
        river_interpolator_gdf=river_interpolator_gdf,
        epsg=epsg_utm31n,
        value_column="waterlevel",
    )
    result = result.to_crs(4326)
    response = result._to_geo()
    return response


@dtv.route("/climate", methods=["POST"])
def climate():
    """compute all climate related quantities"""
    body = flask.request.json
    climate = body["climate"]
    logger.info("Getting network")
    graph = dtv_backend.fis.load_fis_network(url)
    logger.info("Getting interpolators")
    interpolators = dtv_backend.climate.get_interpolators()
    logger.info("Getting edges")
    edges_gdf = dtv_backend.fis.get_edges_gdf(graph=graph)
    logger.info("Getting climate")

    result = dtv_backend.climate.get_variables_for_climate(
        climate=climate, interpolators=interpolators, edges_gdf=edges_gdf
    )
    response = result._to_geo()
    return response


def create_app():
    """Serve"""
    app = flask.Flask("Digital Twin Fairways")
    CORS(app)
    app.register_blueprint(dtv)
    # add routes
    return app


app = create_app()
logger = app.logger
