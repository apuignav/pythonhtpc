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
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(logging.INFO)
    if not format_:
        format_ = "[%(asctime)s] %(name)s::%(levelname)s %(message)s"
    formatter = logging.Formatter()
    stdout.setFormatter(formatter)
    logging.getLogger('htpc').addHandler(stdout)
    return XBMCRPC("XBMC", args.ip, args.httpport, args.tcpport)

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
        shell.interact()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--httpport', action='store', type=int, default=8080)
    parser.add_argument('--tcpport', action='store', type=int, default=9090)
    parser.add_argument('--ip', action='store', type=str, default='192.168.1.120')
    args = parser.parse_args()
    # Start XBMC
    xbmc = initialize_xbmc(args)
    # Run
    start_console(xbmc, globals(), locals())

# EOF
