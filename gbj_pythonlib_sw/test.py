# -*- coding: utf-8 -*-
"""Module for testing programming technics."""
__version__ = '0.1.0'
__status__ = 'Alpha'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = []
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


class Test(object):
    def __init__(self, auth, *args, **kwargs):
        self.auth = auth
        self.server = kwargs.pop('server', 'blynk-cloud.com')
        self.port = kwargs.pop('port', 80)
        self.callbacks = {}

    def __str__(self):
        """Represent instance object as a string."""
        return 'TestClass'

    def __repr__(self):
        """Represent instance object officially."""
        msg = \
        f'Test({repr(self.auth)}, ' \
        f'server={repr(self.server)}, ' \
        f'port={repr(self.port)})'
        return msg

    def ON(self, event):
        o = self
        class Decorator:
            def __init__(self, func):
                self.func = func
                o.callbacks[event] = func
            def __call__(self):
                print('Event = ', event)
                return self.func()
        return Decorator
