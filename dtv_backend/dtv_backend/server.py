import flask
import pandas as pd
import datetime

import dtv_backend.simulate
import dtv_backend.postprocessing
import dtv_backend.fis
import networkx as nx

from flask_cors import CORS


dtv = flask.Blueprint('dtv', __name__)

# TODO: add swaggerui_blueprint
url = "https://zenodo.org/record/4578289/files/network_digital_twin_v0.2.pickle?download=1"

@dtv.route('/')
def home():
    return {"message": "Welcome to the Digital Twin Fairways"}


@dtv.route('/simulate', methods=['POST'])
def simulate():
    config = flask.request.json
    result = dtv_backend.simulate.run(config)
    log_df = pd.DataFrame(result['operator'].logbook)
    log_json = dtv_backend.postprocessing.log2json(log_df)
    env = result["env"]
    result = {
        "log": log_json,
        "config": config,
        "env": {
            "epoch": env.epoch.timestamp(),
            "epoch_iso": env.epoch.isoformat(),
            "now": env.now,
            "now_iso": datetime.datetime.fromtimestamp(env.now).isoformat()
        }
    }
    return flask.jsonify(result)

@dtv.route('/find_route', methods=['POST'])
def find_route():
    """return a the route that passes through the `{"waypoints": ["node", "node"]}` """
    body = flask.request.json
    waypoints = body["waypoints"]
    network = dtv_backend.fis.load_fis_network(url)
    route = dtv_backend.fis.calculate_waypoints_route(network, waypoints)
    length = nx.path_weight(network, route, 'length_m')

    structures = []

    structure_types = {
        'S': 'Structure',
        'L': 'Lock',
        'B': 'Bridge'
    }

    length_m_sum = 0
    for e in zip(route[:-1], route[1:]):
        edge = network.edges[e]
        length_m_sum += edge['length_m']
        # we found a structure
        if e[0][0] == e[1][0] and e[0][0] in ['S', 'B', 'L']:
            row = {
                'length_m_sum': length_m_sum,
                'e': e,
                'n': e[0],
                'type': structure_types[e[0][0]]
            }
            structures.append(row)


    return {
        "waypoints": waypoints,
        "route": route,
        "length": length,
        "structures": structures
    }






def create_app():
    """Serve"""
    app = flask.Flask('Digital Twin Fairways')
    CORS(app)
    app.register_blueprint(dtv)
    # add routes
    return app

app = create_app()
