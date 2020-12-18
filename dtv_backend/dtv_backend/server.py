import flask

import dtv_backend.simulate
import dtv_backend.postprocessing

dtv = flask.Blueprint('dtv', __name__)

# TODO: add swaggerui_blueprint

@dtv.route('/')
def home():
    return {"message": "Welcome to the Digital Twin Fairways"}


@dtv.route('/simulate')
def simulate():
    input = flask.request.json()
    result = dtv_backend.simulate.run()
    log_json = dtv_backend.posptprocessing.log2json(result['operator'].logbook)
    return log_json


def create_app():
    """Serve"""
    app = flask.Flask('Digital Twin Fairways')
    app.register_blueprint(dtv)
    # add routes
    return app

app = create_app()
