from contextlib import ContextDecorator
import datetime
import itertools

import simpy

from opentnsim import core

# global counter that you can iterate over
COUNT = itertools.count()


class LogDecorator(ContextDecorator):
    def __init__(self, env, logbook, message, **kwargs):
        """initialize the logbook"""
        super().__init__()
        self.env = env
        self.logbook = logbook
        self.message = message
        self.kwargs = kwargs

        self.activity_id = next(COUNT)

    def log_entry(
        self,
        message=None,
        timestamp=None,
        value=None,
        geometry=None,
        activity_id=None,
        activity_state=None,
        **kwargs
    ):
        entry = {
            "Message": message,
            "Timestamp": datetime.datetime.utcfromtimestamp(timestamp),
            "Value": value,
            "geometry": geometry,
            "ActivityID": activity_id or next(COUNT),
            "ActivityState": activity_state,
            "Meta": kwargs,
        }
        self.logbook.append(entry)

    def __enter__(self):
        """log a start message on entrance"""
        kwargs = {}
        kwargs.update(self.kwargs)
        self.log_entry(
            message=self.message,
            timestamp=self.env.now,
            activity_id=self.activity_id,
            state="START",
            **self._get_meta()
        )
        return self

    def __exit__(self, *exc):
        """log a stop message on exit"""
        self.log_entry(
            message=self.message,
            timestamp=self.env.now,
            activity_id=self.activity_id,
            state="STOP",
            **self._get_meta()
        )
        return False

    def _get_meta(self):
        """return metadata based on kwargs with some extras:
        - if value is a container, get the current level
        - if source/destination is a container, get the current level
        - if self has a geometry. get the current geometry
        """
        kwargs = {}
        kwargs.update(self.kwargs)

        # store source and destination level
        for key in ("source", "destination"):
            if key in kwargs:
                if isinstance(kwargs[key], simpy.resources.container.Container):
                    kwargs[key + "_level"] = kwargs[key].level
        if "value" in kwargs:
            if isinstance(kwargs["value"], simpy.resources.container.Container):
                kwargs["value"] = kwargs["value"].level
        if hasattr(self, "geometry"):
            kwargs["geometry"] = self.geometry
        return kwargs


class HasLog(core.Identifiable, core.SimpyObject):
    """class that provides a log function for building a logbook"""

    # global logbook
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.env, "logbook"):
            # get logbook from environment
            self.logbook = self.env.logbook
        else:
            # share logbook with environment
            self.logbook = []
            self.env.logbook = self.logbook


    def log_context(self, **kwargs):
        # already fill in the logbook  and environment
        return LogDecorator(
            logbook=self.logbook, env=self.env, actor=self, actor_id=self.id, **kwargs
        )
