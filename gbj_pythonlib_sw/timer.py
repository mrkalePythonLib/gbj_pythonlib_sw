# -*- coding: utf-8 -*-
"""Module for creating a timer and setting its prescalers.

A prescaler can be considered as a timer period divider and can run its own
callbacks separately from the timer's callbacks.

"""
__version__ = '0.4.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2018-2019, ' + __author__
__credits__ = ['Kris Dorosz']
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


import threading
import logging


###############################################################################
# Variables
###############################################################################
timers = {}
"""dict: Registration storage of timers."""


###############################################################################
# Functions
###############################################################################
def register(timer):
    """Store a timer object in the registration dictionary.

    Arguments
    ---------
    timer : object
        Object of a timer that is used as a value in timers registration
        dictionary.
        - The ``name`` attribute of the object is used as a timer name.
        - If name already exists in the dictionary, the timer is updated.

    """
    if timer is None or not isinstance(timer, Timer):
        return
    timers[timer.name] = timer


def unregister(name):
    """Remove a timer with provided name from the registration dictionary."""
    if name is None:
        return
    name = str(name)
    try:
        timer = timers.pop(name)
        timer.stop()
    except KeyError:
        pass


def start_all():
    """Start all registered timers."""
    for timer in timers:
        timers[timer].start()


def stop_all():
    """Stop all registered timers."""
    for timer in timers:
        timers[timer].stop()


###############################################################################
# Classes
###############################################################################
class Timer(object):
    """Creating and registering a timer.

    Arguments
    ---------
    period : float
        Mandatory positive float interval of the timer in seconds. If other
        type is provided, it is converted to an absolute float.
    callback : function or tuple of functions
        Mandatory one or more functions in role of callbacks that the timer
        calls when expires.

    Keyword Arguments
    -----------------
    count : int
        Positive integer number of desired shots of the timer. If other
        type is provided, it is converted to absolute integer.
        If it is not defined, the timer is processed as periodic one with
        endless running.
    name : str
        Name of the timer incorporated to its object. If none is provided,
        the concatenation of its class name and order is used.

    Notes
    -----
    - If the timer is created without defined count of shots, it is a periodic
      timer marked with ``R`` as ``repeating`` in the string instance
      representation.
    - If the timer is created with count greater than 1, it is a countdown
      timer marked with ``C`` as ``countdown`` in the string instance
      representation.
    - If the timer is created with count equal 1, it is an one-shot timer
      marked with ``O`` as ``oneshot`` in the string instance representation.
    - Keyword arguments not listed here are passed to the callback function(s).

    See Also
    --------
    register_timer : Registration of timers.

    """

    _instances = 0
    """int: Number of class instances."""

    def __init__(self, period, callback, *args, **kwargs):
        """Create the class instance - constructor."""
        type(self)._instances += 1
        self._args = args
        self._kwargs = kwargs
        #
        self._period = abs(float(period))
        # Sanitize callbacks
        if not isinstance(callback, tuple):
            callback = tuple([callback])
        self._callbacks = callback
        # Sanitize name
        self._order = type(self)._instances
        self._count = self._kwargs.pop('count', None)
        self.__name = self._kwargs.pop('name',
            f'{self.__class__.__name__}{self._order}')
        #
        self._prescalers = []
        self._timer = None
        self._stopping = False
        self._repeate = True
        # Mark timer
        if self._count is None:
            self._mark = 'R'
        else:
            self._count = abs(int(self._count))
            if self._count > 1:
                self._mark = 'C'
            elif self._count == 1:
                self._mark = 'O'
                self._repeate = False   # Flag about on-shot timer
        # Register timer
        register(self)
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug(
            'Instance of %s created: %s',
            self.__class__.__name__, str(self)
        )

    def __del__(self):
        """Clean after instance destroying - destructor.

        Notes
        -----
        - In this method the object self._logger does not already exist,
          so that logging is not possible.

        """
        type(self)._instances -= 1

    def __str__(self):
        """Represent instance object as a string.

        All the relevant timer's parameters are involved in the string, i.e.,
        period, mark, and instance number.

        """
        msg = \
            f'{self.__name}(' \
            f'{float(self._period)}s-' \
            f'{self._mark}' \
            f'{"" if self._count is None else str(self._count)}-' \
            f'{self._order})'
        return msg

    def __repr__(self):
        """Represent instance object officially."""
        if len(self._callbacks) > 1:
            cblist = [c.__name__ for c in self._callbacks]
            cb = f'({", ".join(cblist)})'
        else:
            cb = self._callbacks[0].__name__
        msg = \
            f'{self.__class__.__name__}(' \
            f'period={repr(self._period)}, ' \
            f'callback={cb}, ' \
            f'count={repr(self._count)}, ' \
            f'name={repr(self.__name)}, ' \
            f'args={repr(self._args)}, ' \
            f'kwargs={repr(self._kwargs)})'
        return msg

    @property
    def name(self):
        """Name of the timer."""
        return self.__name

    @property
    def prescalers(self):
        """Dictionary of prescalers."""
        if hasattr(self, '_prescalers'):
            return self._prescalers

    def _create_timer(self):
        """Create new timer object and start it."""
        if not self._stopping:
            self._timer = threading.Timer(self._period, self._run_callback)
            self._timer.name = self.__name
            self._timer.start()

    def _run_callback(self):
        """Run external instance callback.

        Other Parameters
        ----------------
        exec_last : bool
            Flag about last calling at countdown timers injected to all
            callback function as a keyword argument.

        """
        if self._callbacks is None:
            return
        if self._count is not None:
            if self._count <= 0:
                return
            if self._count == 1:
                self._repeate = False
        try:
            # Call basic timer callback
            for callback in self._callbacks:
                self._logger.debug(
                    'Main callback %s of %s launched',
                    callback.__name__, str(self)
                )
                callback(
                    *self._args,
                    exec_last=not self._repeate,
                    **self._kwargs
                )
            # Count down prescalers and call callbacks of expired ones
            for prescaler in self._prescalers:
                prescaler['counter'] -= 1
                if prescaler['counter'] <= 0:
                    prescaler['counter'] = prescaler['factor']
                    callbacks = prescaler['callbacks']
                    for callback in callbacks:
                        self._logger.debug(
                            'Prescaler %d callback %s of %s launched',
                            prescaler['factor'],
                            callback.__name__, str(self)
                        )
                        callback(
                            *prescaler['args'],
                            exec_last=not self._repeate,
                            **prescaler['kwargs']
                        )
        except Exception:
            self._logger.error('Running callbacks of %s failed:',
                               str(self), exc_info=True)
        finally:
            if self._repeate:
                self._create_timer()
                if self._count is not None:
                    self._count -= 1

    def start(self):
        """Create timer thread object and store it in the instance."""
        if (self._count or 1) <= 0:
            self._logger.debug('%s not started', str(self))
            return
        else:
            self._create_timer()
            self._logger.debug('%s started', str(self))

    def stop(self):
        """Destroy timer thread object."""
        self._stopping = True
        if self._timer is not None:
            self._timer.cancel()
            self._logger.debug('%s stopped', str(self))

    def prescaler(self, factor, callback, *args, **kwargs):
        """Register a callback function called at each factor tick.

        Arguments
        ---------
        factor : int
            Mandatory positive integer as a divider of the timer's period.
            It is truncated to an absolute integer and ignored, if it results
            to less than 2. The factor is used as a key in registration
            dictionary of prescalers.
        callback : function or tuple of functions
            Mandatory one or more functions calling by the timer at each
            factor-th period.
        args : tuple
            Additional positional arguments passed to the callback(s).

        Keyword Arguments
        -----------------
        kwargs : dict
            Additional keyword arguments passed to the callback(s).

        Notes
        -----
        - The prescaler method enables launching a specific callback or more
          callbacks at multiple timer periods and acts as a frequency divider.
        - Prescale factor equal 1 is useless, because it is equivalent to basic
          timer callback or tuple of them. In this case it is ignored.
        - The prescaler method can be called multiple times. For the same
          factor the corresponding callback is updated including its arguments.
          If none factor is provided, the prescaler is removed.
        - None of prescalers is launched, if timer's callback is not defined or
          timer is one-time one.
        - All prescalers are called at random order, but usually in order of
          their registration.

        """
        factor = abs(int(factor))
        if factor < 2:
            return
        # Sanitize callbacks
        if not isinstance(callback, tuple):
            callback = tuple([callback])
        # Find existing prescaler and remove or update it
        new = True
        for i, prescaler in enumerate(self._prescalers):
            if prescaler['factor'] == factor:
                if callback is None:
                    self._prescalers.pop(i)
                else:
                    prescaler['callbacks'] = callback
                    prescaler['args'] = args
                    prescaler['kwargs'] = kwargs
                new = False
                break
        # Create new prescaler
        if new:
            prescaler = {
                'counter': factor,
                'factor': factor,
                'callbacks': callback,
                'args': args,
                'kwargs': kwargs,
            }
            self._prescalers.append(prescaler)
