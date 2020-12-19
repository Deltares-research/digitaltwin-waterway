import flask
import pandas as pd
import datetime

import dtv_backend.simulate
import dtv_backend.postprocessing

from flask_cors import CORS


dtv = flask.Blueprint('dtv', __name__)

# TODO: add swaggerui_blueprint

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


def create_app():
    """Serve"""
    app = flask.Flask('Digital Twin Fairways')
    CORS(app)
    app.register_blueprint(dtv)
    # add routes
    return app

app = create_app()
