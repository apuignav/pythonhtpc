#!/usr/bin/env python
# =============================================================================
# @file   xbmcrpc.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   02.03.2014
# =============================================================================
"""JSON-RPC interaction with XBMC."""
#https://github.com/gazpachoking/jsonref

import symmetricjsonrpc

from pythonhtpc.core import RPCServer

class XBMCRPC(RPCServer):
    class RPCClient(symmetricjsonrpc.RPCClient):
        class Request(symmetricjsonrpc.RPCClient.Request):
            def dispatch_notification(self, notification):
                # Handle callbacks from the server
                method = notification.pop('method', None)
                params = notification.pop('params', None)
                self.parent._notification_callback(method, params)

        def set_notification_callback(self, notification_callback):
            self._notification_callback = notification_callback
            return self

    def __init__(self, name, address, http_port=8080, tcp_port=9090):
        super(XBMCRPC, self).__init__(name)
        self._address = (address, http_port, tcp_port)
        schema = self._discover()
        self._method_config, self._notification_config = schema['methods'], schema['notifications']
        for method in self._method_config:
            self._methods.append(method)
        for notification in self._notification_config:
            self._published_notifications.append(notification)

    def wait(self):
        try:
            while True:
                self._rpc.join(100)
        except KeyboardInterrupt:
            pass
        #except:
            #raise
        finally:
            self.stop()

    def stop(self):
        self.logger.debug("Shutting down RPC")
        self._rpc.shutdown()
        self._rpc.join()

    def _discover(self):
        """Discover methods and schema from the http jsonrpc."""
        def process_schema(schema):
            """See http://forum.xbmc.org/showthread.php?tid=190653 for details."""
            processed_schema = {'methods': {}, 'notifications': {}}
            for method, config in schema['methods'].items():
                params = dict([(element.pop('name'), element) for element in config['params']])
                processed_schema['methods'][method] = {'description': config['description'],
                                                    'params': {'type': 'object', 'properties': params},
                                                    'returns': config['returns'],
                                                    }
            # Hack for notifications
            processed_schema['methods']['JSONRPC.Version']['returns'] = {'type': 'object',
                                                                        'properties': {'version': {'properties': processed_schema['methods']['JSONRPC.Version']['returns']['properties']}}
                                                                        }
            processed_schema['notifications']['GUI.OnScreensaverActivated'] = processed_schema['notifications']['VideoLibrary.OnCleanStarted']
            processed_schema['notifications']['GUI.OnScreensaverActivated']['description'] = "The screensaver has been activated."
            processed_schema['notifications']['GUI.OnScreensaverDeactivated'] = processed_schema['notifications']['VideoLibrary.OnCleanStarted']
            processed_schema['notifications']['GUI.OnScreensaverDeactivated']['description'] = "The screensaver has been deactivated."
            # Ref resolving!
            return processed_schema

        from json import loads
        import urllib2
        address, port, _ = self._address
        description_address = 'http://%s:%s/jsonrpc' % (address, port)
        try:
            response = urllib2.urlopen(description_address)
            schema = loads(response.read())
        except:
            self.logger.exception("Error loading schema from http://%s:%s/jsonrpc" % (address, port))
            raise
        response.close()
        # Return processed schema
        return process_schema(schema)

    def _init_rpc(self):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #  Connect to the server
        address, _, port = self._address
        sock.connect((address, port))
        # Create a client thread handling for incoming requests
        self.__socket = sock
        return XBMCRPC.RPCClient(sock).set_notification_callback(self.notification_callback)


    def _execute_method(self, method, params, wait_for_response):
        from validictory import validate
        # Find config
        config = self._method_config.get(method, None)
        if not config:
            self.logger.error("I don't have any configuration for method %s" % method)
            return None
        # Check parameters
        try:
            pass
            #self.logger.debug("Validating %s against %s" % (params, config['params']))
            #validate(params, config['params'])
        except:
            self.logger.exception("Error validating parameters:")
            return None
        try:
            result = self._rpc.request(method, wait_for_response=wait_for_response, params=params)
            #if isinstance(result, dict):
                #result = result[result.keys()[0]]
        except:
            self.logger.exception("Error sending request to XBMC:")
            return None
        # Check returns
        try:
            #self.logger.debug("Validating %s against %s" % (result, config['returns']))
            validate(result, config['returns'])
            return result
        except:
            self.logger.exception("Error validating answer from XBMC:")
            return None

    def notification_callback(self, notification, value):
        self.logger.debug("Received notification %s with value %s" % (notification, value))
        try:
            if notification in self._subscribed_notifications:
                params = self._process_notification(notification, value)
                self.notify(notification, params)
        except:
            self.logger.exception("Problem processing notification %s with value %s:" % (notification, value))

    def _process_notification(self, notification, value):
        from validictory import validate
        validate(value, {'params': self._notification_config[notification]['params']})
        return value

class XBMCCLI(XBMCRPC):
    pass

#class XBMCRPC(object):
    #class XBMCNamespace(object):
        #class XBMCMethod(object):
            #def __init__(self, name, **config):
                #self.name = name
                #self._config = config

            #def __call__(self, **kwargs):
                #from jsonschema import validate
                #print self.name, kwargs
                #validate(self._config, kwargs)

            #def help(self):
                #print self._config['description']
                #print 'Parameters:', self._config['params']

        #def __init__(self, name, parent):
            #self.name = name
            #self.methods = {}
            #self._parent = parent

        #def add_method(self, method, schema):
            #self.methods[method] = XBMCRPC.XBMCNamespace.XBMCMethod("%s.%s" % (self.name, method), **schema)

        #def add_notification(self, notification, schema):
            #raise NotImplementedError()

        #def __getattr__(self, value):
            #return self.methods.get(value, None)

    #def __init__(self, address, http_port=8080, tcp_port=9090):
        #self._address = (address, http_port, tcp_port)
        #schema = self._discover()
        #self._methods, self._notifications = self._build_hierarchy(schema)

    #def _discover(self):
        #"""Discover methods and schema from the http jsonrpc."""
        #from json import loads
        #import urllib2
        #address, port, _ = self._address
        #description_address = 'http://%s:%s/jsonrpc' % (address, port)
        #response = urllib2.urlopen(description_address)
        #schema = loads(response.read())
        #response.close()
        #return schema

    #def _build_hierarchy(self, schema):
        ## Build methods
        #methods = {}
        #for method, method_config in schema['methods'].items():
            #namespace, method_name = method.split('.')
            #if not hasattr(self, namespace):
                #setattr(self, namespace, XBMCRPC.XBMCNamespace(namespace, self))
            #getattr(self, namespace).add_method(method_name, method_config)
            #methods[method] = getattr(getattr(self, namespace), method_name)
        ## Get list of notifications
        #notifications = schema['notifications'].items()
        #return methods, notifications

    #def available_methods(self):
        #return self._methods

    #def execute_method(self, name, **kwargs):
        #method = self._methods.get(name, None)
        #if not method:
            #raise ValueError("Unknown method %s" % name)
        #return method(**kwargs)

    #def register_notification(self, name, callback):
        ##if not name in
        #for notification, notification_config in schema['notifications'].items():
            #namespace, method_name = method.split('.')
            #if not hasattr(self, namespace):
                #setattr(self, namespace, XBMCRPC.XBMCNamespace(namespace, self))
            #getattr(self, namespace).add_method(method_name, method_config)
            #methods[method] = getattr(getattr(self, namespace), method_name)
        #pass

if __name__ == '__main__':
    # Configure logging (ALWAYS needed!)
    import logging
    import sys
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(name)s::%(levelname)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s")
    stdout.setFormatter(formatter)
    logging.getLogger('htpc').addHandler(stdout)
    # Now run
    with XBMCRPC("RaspiXBMC", "192.168.1.120") as xbmc:
        print xbmc.execute_method('JSONRPC.Ping')
        print xbmc.execute_method('JSONRPC.Version')
        # xbmc.execute_method("Addons.ExecuteAddon", params={'addonid': 'script.xbmc.subtitles'})
    # Or run until Ctrl+C
    #print xbmc.execute_method('JSONRPC.Ping', True)
    #print xbmc.execute_method('JSONRPC.Version', True)
    #xbmc.stop()
    #xbmc.wait()

# EOF
