# -*- coding: utf-8 -*-
"""Module for auxilliary utilities and functions."""
__version__ = "0.1.0"
__status__ = "Beta"
__author__ = "Libor Gabaj"
__copyright__ = "Copyright 2019, " + __author__
__credits__ = []
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "libor.gabaj@gmail.com"


import psutil


###############################################################################
# Functions
###############################################################################
def check_service(script):
    """Detect running script as a service.

    Arguments
    ---------
    script : str
        Name of a script process to be checked or script file name without
        path and extension.

    Returns
    -------
    bool
        Flag about running script as a service.

    """
    ls = []
    for p in psutil.process_iter(attrs=['name']):
        if p.info['name'] == script:
            ls.append(p)
    return len(ls) > 0
