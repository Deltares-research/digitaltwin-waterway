#!/usr/bin/env python3
#!/usr/bin/env python3
#
import datetime

import simpy
import geojson
import geopandas as gpd
import pandas as pd

import pytest

import dtv_backend.compat
import dtv_backend.simulate


@pytest.fixture
def config():
    with open("tests/user/2022-10-21-config.json") as f:
        config = geojson.load(f)
    return config


@pytest.fixture
def quantity_df(config):
    return dtv_backend.simulate.create_quantity_df(config)


@pytest.fixture
def env():
    t_start = datetime.datetime(2020, 1, 1)
    env = simpy.Environment(initial_time=t_start.timestamp())
    env.epoch = t_start
    env.FG = None
    # run for a day
    return env


def test_energy(env, quantity_df):
    # No data
    test_cases = pd.DataFrame(
        [
            {"e": ("18008360", "18008345"), "expected": 6},
            {"e": ("B27001_A", "B13169_B"), "expected": 6},
            {"e": ("L53479_A", "8864929"), "expected": 1.3331793601626796},
            {"e": ("B14843_A", "B14843_B"), "expected": 6},
        ]
    )

    observed = []
    for i, test_case in test_cases.iterrows():
        ship = dtv_backend.compat.CanWork(env=env, name="test-ship", capacity=10)
        ship.quantity_df = quantity_df
        result = ship.get_waterdepth(test_case.e)
        observed.append(result)
    test_cases["observed"] = observed

    print(test_cases["observed"], test_cases["expected"])
    pd.testing.assert_series_equal(
        test_cases["observed"], test_cases["expected"], check_names=False
    )
