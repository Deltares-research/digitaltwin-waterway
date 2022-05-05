#!/usr/bin/env python3
#
import datetime
import simpy

import pytest

import dtv_backend.scheduling


@pytest.fixture
def env():
    t_start = datetime.datetime(2020, 1, 1)
    env = simpy.Environment()
    env.epoch = t_start
    # run for a day
    env.timeout(3600 * 24)
    env.run()
    return env


@pytest.fixture
def has_timeboard(env):
    shift_start_time = datetime.time(6, 0)
    shift_end_time = datetime.time(22, 0)
    has_timeboard = dtv_backend.scheduling.HasTimeboard(
        env, shift_start_time=shift_start_time, shift_end_time=shift_end_time
    )
    return has_timeboard


def test_timeboard_created(has_timeboard):
    # timeboard should be created
    assert hasattr(has_timeboard, "timeboard")


def test_timeboard_next_on_duty(has_timeboard):
    # timeboard should be created
    # we should be able to find a next off duty time
    assert (
        has_timeboard.next_off_duty > has_timeboard.current_time
    ), "next off duty should be in the future"
    # and next on_duty time. Which should be in the future.
    assert (
        has_timeboard.next_on_duty > has_timeboard.current_time
    ), "next on duty should be in the future"
