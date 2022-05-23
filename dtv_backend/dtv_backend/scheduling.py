"""This module implements scheduling functionality using the python timeboard module"""

import datetime

import timeboard as tb

import dtv_backend.logbook
from typing import Optional


class HasTimeboard(dtv_backend.logbook.HasLog):
    """Add timeboard information (work schedule)"""

    def __init__(
        self,
        env,
        shift_start_time: Optional[datetime.time] = None,
        shift_end_time: Optional[datetime.time] = None,
        *args,
        **kwargs,
    ):
        super().__init__(env=env, *args, **kwargs)
        # record the environment because we need the start time
        #self.env = env

        assert hasattr(
            self.env, "epoch"
        ), "environment should have an epoch so that we can compute with dates and times"
        assert isinstance(
            self.env.epoch, datetime.datetime
        ), "environment should have a datetime epoch, for scheduling"

        if shift_start_time is None:
            shift_start_time = datetime.time(6, 0)
        if shift_end_time is None:
            shift_end_time = datetime.time(22, 0)

        self.shift_start_time = shift_start_time
        assert isinstance(
            self.shift_start_time, datetime.time
        ), "start time should be a datetime.time instance"
        self.shift_end_time = shift_end_time
        assert isinstance(
            self.shift_end_time, datetime.time
        ), "end time should be a datetime.time instance"

        self.timeboard = self._create_timeboard()

    def _create_timeboard(self) -> tb.Timeboard:
        """Create a timeboard, a schedule for trips"""

        max_trip_duration = 30
        t_start = self.env.epoch.replace(second=0, hour=0, minute=0, microsecond=0)

        t_end = t_start + datetime.timedelta(days=max_trip_duration)

        a1_schedule = tb.Marker(
            each="D",
            at=[
                {
                    "hours": self.shift_start_time.hour,
                    "minutes": self.shift_start_time.minute,
                },
                {
                    "hours": self.shift_end_time.hour,
                    "minutes": self.shift_end_time.minute,
                },
            ],
        )
        shifts = tb.Organizer(marker=a1_schedule, structure=[0, 1])

        timeboard = tb.Timeboard(
            base_unit_freq="H", start=t_start, end=t_end, layout=shifts
        )
        return timeboard

    @property
    def current_time(self) -> datetime.datetime:
        """get the current time from the environment"""
        return datetime.datetime.fromtimestamp(self.env.now)

    @property
    def current_shift(self) -> tb.Workshift:
        """get the current shift. The shift starts at the"""

        return self.timeboard.get_workshift(self.current_time)

    @property
    def is_on_duty(self) -> bool:
        """is the ship working"""
        return self.current_shift.is_on_duty()

    @property
    def is_off_duty(self) -> bool:
        """is the ship on a break"""
        return self.current_shift.is_on_duty()

    def get_next_shift(self, duty: str) -> tb.Workshift:
        """lookup the next shift given duty ='on' or duty='off'"""

        assert duty in ("off", "on"), "duty should be 'on' or 'off'"

        steps = 0
        if self.current_shift.is_off_duty() and duty == "off":
            steps = 1
        if self.current_shift.is_on_duty() and duty == "on":
            steps = 1
        next_shift = self.current_shift.rollforward(steps=steps, duty=duty)
        return next_shift

    @property
    def next_off_duty(self) -> datetime.datetime:
        """return datetime of next scheduled stop"""
        next_off_duty = self.get_next_shift(duty="off")
        return next_off_duty.start_time

    @property
    def next_on_duty(self) -> datetime.datetime:
        """wait for the next stop"""
        next_on_duty = self.get_next_shift(duty="on")
        return next_on_duty.start_time

    def sleep_if_off_duty(self):
        """sleep until we are on duty again"""
        time_until_duty = datetime.timedelta(seconds=0)
        if self.is_off_duty:
            time_until_duty = self.next_on_duty - self.current_time
        seconds_until_duty = time_until_duty.total_seconds()
        with self.log(message="Sleeping", description=f"Sleeping"):
            yield self.env.timeout(seconds_until_duty)
    
    def sleep_till_next_duty(self):
        """
        sleep until we are on duty again, even if we could still be
        on duty at this moment (i.e. reached a berthing spot right before the
        end of a shift)
        """
        print(f"sleeping start at {self.current_time }")
        time_until_duty = self.next_on_duty - self.current_time            
        seconds_until_duty = time_until_duty.total_seconds()
        with self.log(message="Sleeping", description=f"Sleeping"):
            yield self.env.timeout(seconds_until_duty)
