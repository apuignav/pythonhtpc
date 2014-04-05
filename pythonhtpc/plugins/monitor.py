#!/usr/bin/env python
# =============================================================================
# @file   monitor.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   02.04.2014
# =============================================================================
"""Monitor system."""
import re

from pythonhtpc.core import CronJob
from pythonhtpc.utils.system import run_command

class Monitor(object):
    """Generic monitoring class."""
    def __init__(self, monitor_func):
        self._monitor_func = monitor_func

    def monitor(self):
        return self._monitor_func()

class CPUTempMonitor(Monitor):
    """Monitor CPU Temperature."""
    def __init__(self):
        super(CPUTempMonitor, self).__init__(self.__monitor)

    def __monitor(self):
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp = float(f.readlines()[0].strip('\n'))/1000.0
        return temp

class GPUTempMonitor(Monitor):
    """Monitor GPU Temperature."""
    def __init__(self):
        super(GPUTempMonitor, self).__init__(self.__monitor)
        self._regex = re.compile('temp=([0-9\.]+)')

    def __monitor(self):
        try:
            return float(self._regex.match(run_command('/opt/vc/bin/vcgencmd', 'measure_temp')[0]).group(1))
        except:
            # Regex didn't match
            return 0.0

if __name__ == '__main__':
    _fmt = "%30s = %.1f"
    print _fmt % ("CPU Temp", CPUTempMonitor().monitor())
    print _fmt % ("GPU Temp", GPUTempMonitor().monitor())

# EOF
