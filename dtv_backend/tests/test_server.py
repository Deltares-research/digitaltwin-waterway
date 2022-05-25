#!/usr/bin/env python3
import json
import pathlib

import pytest

import sys
sys.path.append(r"D:\01. Projecten\[130878] DTV vaarwegen\digitaltwin-waterway\dtv_backend")
from dtv_backend.server import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def current_dir_path():
    """Lookup the path of the current file and return the parent"""
    current_file_path = pathlib.Path(__file__)
    return current_file_path.parent


def test_home(client):
    response = client.get("/")
    assert b"Digital" in response.data


def test_v2_simulate(client, current_dir_path):
    with (current_dir_path / "test-berth" / "body.json").open() as f:
        body = json.load(f)

    response = client.post("/v2/simulate", json=body)
    
    # check the status
    assert response.status_code == 200
    
    # check if the response can be read as dict
    try:
        d = json.loads(response.data)
        assert isinstance(d, dict), 'data was not returned as a dict'
    except Exception as e:
        raise
    
