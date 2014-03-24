#!/usr/bin/env python
# =============================================================================
# @file   core.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   09.03.2014
# =============================================================================
""""""

from pebble import thread
from apscheduler.scheduler import Scheduler

class HTPCObject(object):
    """Base object for HTPClib.

    Provides basic notification capabilities.

    """
    def __init__(self, name):
        super(HTPCObject, self).__init__()
        self.name = name
        # Notifications are {name: config} pairs (config can be None)
        self._published_notifications = []
        # Subscribed are {name: [list of callbacks]} pairs
        self._subscribed_notifications = {}
        # Logging
        import logging
        self.logger = logging.getLogger('htpc.%s' % name)

    def start(self):
        raise NotImplementedError("I don't know how to start the object!")

    def stop(self):
        raise NotImplementedError("I don't know how to stop the object!")

    def __enter__(self):
        return self.start()

    def __exit__(self, ext_type, exc_value, traceback):
        self.stop()

    def available_notifications(self):
        return self._published_notifications

    def get_notification_info(self, notification):
        raise NotImplementedError("I don't know how to give you information")

    def add_notification_subscription(self, name, callback):
        if not name in self._published_notifications:
            return None
        if not name in self._subscribed_notifications:
            self._subscribed_notifications[name] = []
        self._subscribed_notifications[name].append(callback)
        return name

    @thread
    def notify(self, notification, value):
        if not (notification in self._subscribed_notifications):
            # Nobody is subscribed
            return None
        self.logger.debug("Sending notification %s with value %s" % (notification, value))
        for callback in self._subscribed_notifications[notification]:
            callback(self, value)

class RPCServer(HTPCObject):
    # Server is notifications + possibility to execute methods
    def __init__(self, name):
        super(RPCServer, self).__init__(name)
        # Methods are {name: config} pairs (config can be None)
        self._methods = []
        # RPC is created on start()
        self._rpc = None

    def start(self):
        self.logger.debug("Initializing RPC")
        self._rpc = self._init_rpc()
        return self

    def _init_rpc(self):
        self.logger.critical("I don't know how to start the RPC!")
        raise NotImplementedError("I don't know how to start the RPC!")

    def _run(self):
        self.logger.critical("I don't know how to run the RPC!")
        raise NotImplementedError("I don't know how to run the RPC!")

    def stop(self):
        # Perform cleanup here
        pass

    def available_methods(self):
        return self._methods

    def get_method_info(self, method):
        self.logger.critical("I don't know how to give you information yet")
        raise NotImplementedError("I don't know how to give you information yet")

    def execute_method(self, method, params=None, wait_for_response=True):
        if params is None:
            params = {}
        self.logger.debug("Executing method %s with parameters %s" % (method, params))
        if not method in self._methods:
            self.logger.error("Unknown method %s" % method)
            return None
        return self._execute_method(method, params, wait_for_response)

    def _execute_method(self, method, params, wait_for_response):
        self.logger.critical("I don't know how to execute methods")
        raise NotImplementedError("I don't know how to execute methods")

class EventHandler(HTPCObject):
    # {RPC type: {notification: callback}}
    _notifications_to_register = {}
    # List
    _notifications_to_publish = []
    def __init__(self, name, *rpcs):
        super(EventHandler, self).__init__(name)
        # {RPC name: RPC object} pairs
        self._connected_rpcs = {}
        for rpc in rpcs:
            self._registered_notifications = self.connect_to_rpc(rpc)
        self._subscribed_notifications = {}
        # Initialize notifications to offer
        for notification in self._notifications_to_publish:
            self._published_notifications.append(notification)

    def connect_to_rpc(self, rpc_object):
        # Connect
        rpc_name = rpc_object.name
        if rpc_name in self._connected_rpcs:
            self.logger.error("Already registered to RPC %s" % rpc_name)
            return 0
        else:
            self._connected_rpcs[rpc_name] = rpc_object
        # Register to notifications
        rpc_type = type(rpc_object)
        notifications = self._notifications_to_register.get(rpc_type, dict())
        registered_notifications = 0
        for notification_name, callback in notifications.items():
            if rpc_object.add_notification_subscription(notification_name, callback):
                registered_notifications += 1
        return registered_notifications

    def start(self):
        if len(self._connected_rpcs) == 0 or self._registered_notifications == 0:
            self.logger.critical("EventHandler %s is not handling anything! Raising exception...")
            raise ValueError("EventHandler %s is not handling anything!")

    def stop(self):
        pass

class CronJob(HTPCObject):
    # List
    _notifications_to_publish = []
    def __init__(self, name, schedule):
        super(CronJob, self).__init__(name)
        # Configure scheduler
        self.scheduler = Scheduler(schedule)
        day, hour, minute = schedule
        self.scheduler.add_cron_job(self.run, day=day, hour=hour, minute=minute)
        # Initialize notifications to offer
        for notification in self._notifications_to_publish:
            self._published_notifications.append(notification)

    def start(self):
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()

    def run(self):
        raise NotImplementedError("I don't know how to run the cron job!")

# EOF
