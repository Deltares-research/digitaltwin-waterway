from contextlib import ContextDecorator
import datetime
import itertools
import uuid

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

    def log_entry(self, message=None, timestamp=None, value=None, geometry=None, activity_id=None, activity_state=None, **kwargs):
        entry = {
            "Message": message,
            "Timestamp": datetime.datetime.utcfromtimestamp(timestamp),
            "Value": value,
            "geometry": geometry,
            "ActivityID": activity_id or next(COUNT),
            "ActivityState": activity_state,
            "Meta": kwargs
        }
        self.logbook.append(entry)

    def __enter__(self):
        """log a start message on entrance"""
        self.log_entry(
            message=self.message,
            timestamp=self.env.now,
            activity_id=self.activity_id,
            state='START',
            **self.kwargs
        )
        return self

    def __exit__(self, *exc):
        """log a stop message on exit"""
        self.log_entry(
            message=self.message,
            timestamp=self.env.now,
            activity_id=self.activity_id,
            state='STOP',
            **self.kwargs
        )
        return False


class HasLog(object):
    """class that provides a log function for building a logbook"""
    # global logbook
    logbook = []
    def __init__(self, env, *args, **kwargs):
        self.env = env
        self.id = str(uuid.uuid4())


    def log(self, **kwargs):
        # already fill in the logbook  and environment
        return LogDecorator(
            logbook=self.logbook,
            env=self.env,
            actor=self,
            actor_id=self.id,
            **kwargs
        )
