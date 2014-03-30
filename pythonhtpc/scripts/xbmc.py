#!/usr/bin/env python
# =============================================================================
# @file   xbmc.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   30.03.2014
# =============================================================================
"""Run and interact with XBMC on command line,"""

import sys
import argparse
import logging

import code
import readline
import rlcompleter

from pythonhtpc.rpcs.xbmcrpc import XBMCRPC

def initialize_xbmc(args, format_=None):
    if args.loglevel.lower() == 'debug':
        log_level = logging.DEBUG
    elif args.loglevel.lower() == 'info':
        log_level = logging.INFO
    elif 'warn' in args.loglevel.lower():
        log_level = logging.WARNING
    elif args.loglevel.lower() == 'error':
        log_level = logging.ERROR
    elif args.loglevel.lower() == 'critical':
        log_level = logging.CRITICAL
    else:
        print "Didn't understand your desired logging level, switching to DEBUG"
        log_level = logging.DEBUG
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(log_level)
    if not format_:
        format_ = "[%(asctime)s] %(name)s::%(levelname)s %(message)s"
    formatter = logging.Formatter(format_)
    stdout.setFormatter(formatter)
    logging.getLogger('htpc').addHandler(stdout)
    return XBMCRPC("XBMC", args.ip, args.httpport, args.tcpport)

def decorate_xbmc(xbmc):
    class Namespace(object):
        def __init__(self, name, parent, methods):
            self._name = name
            self._parent = parent
            self.configure_methods(methods)

        def configure_methods(self, method_list):
            def wrapper(func_name):
                from functools import wraps
                @wraps(self._parent.execute_method)
                def method_caller(*args, **kwargs):
                    return self._parent.execute_method('%s.%s' % (self._name, func_name), *args, **kwargs)
                return method_caller
            for method in method_list:
                setattr(self, method, wrapper(method))

    methods = {}
    for method in xbmc.get_available_methods():
        namespace, method = method.split('.')
        if not namespace in methods:
            methods[namespace] = []
        methods[namespace].append(method)
    for namespace, method_list in methods.items():
        setattr(xbmc, namespace, Namespace(namespace, xbmc, method_list))
    return xbmc

def start_console(xbmc, _globals, _locals):
    """Opens interactive console with current execution state.

    Call it with: `console.open(xbmc, globals(), locals())`

    """
    context = _globals.copy()
    context.update(_locals)
    readline.set_completer(rlcompleter.Completer(context).complete)
    readline.parse_and_bind("tab: complete")
    shell = code.InteractiveConsole(context)
    with xbmc:
        shell.interact('Welcome to XBMC CLI! Your XBMC is in variable xbmc')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--httpport', action='store', type=int, default=8080)
    parser.add_argument('--tcpport', action='store', type=int, default=9090)
    parser.add_argument('--ip', action='store', type=str, default='192.168.1.120')
    parser.add_argument('--loglevel', action='store', type=str, default='INFO')
    args = parser.parse_args()
    # Start XBMC
    xbmc = decorate_xbmc(initialize_xbmc(args))
    # Run
    start_console(xbmc, globals(), locals())

# EOF
