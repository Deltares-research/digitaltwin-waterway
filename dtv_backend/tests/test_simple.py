#!/usr/bin/env python3

import datetime

import simpy
import shapely.geometry

import pytest

import dtv_backend.simple


@pytest.fixture
def env():
    t_start = datetime.datetime(2020, 1, 1)
    env = simpy.Environment(initial_time=t_start.timestamp())
    env.epoch = t_start
    return env


@pytest.fixture
def ship(env):
    geometry = shapely.geometry.Point(53, 2)
    name = "ship"
    ship = dtv_backend.simple.Ship(env=env, name=name, geometry=geometry)
    return ship


def test_ship(ship):
    """test ship features"""
    assert hasattr(ship, "logbook"), "ship should have a logbook"
    assert hasattr(ship, "timeboard"), "ship should have a timeboard"
