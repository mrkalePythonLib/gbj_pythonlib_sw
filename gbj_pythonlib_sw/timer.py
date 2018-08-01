#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Module for creating a timer and its prescalers."""
__version__ = "0.2.0"
__status__ = "Development"
__author__ = "Libor Gabaj"
__copyright__ = "Copyright 2018, " + __author__
__credits__ = ["Kris Dorosz"]
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "libor.gabaj@gmail.com"


import threading
import logging


###############################################################################
# Variables
###############################################################################
timers = {}     # Dictionary of registered timers


###############################################################################
# Functions
###############################################################################
def register_timer(name, timer=None):
    """Store a timer object in the dictionary.

    Positional arguments:
    ---------------------
    name -- key name of a timer
    timer -- value object of a timer. If name already exists in the dictionary,
             the timer is update. If none and name already exists, the timer
             is stopped and removed from the dictionary.
    """
    if not name:
        return
    if timer is None:
        try:
            timer = timers.pop(name)
            timer.stop()
        except KeyError:
            pass
    else:
        try:
            timers[name] = timer
        except KeyError:
            pass


def start_timers():
    """Start all registered timers."""
    for timer_name in timers:
        timers[timer_name].start()


def stop_timers():
    """Stop all registered timers."""
    for timer_name in timers:
        timers[timer_name].stop()


###############################################################################
# Classes
###############################################################################
class Timer(object):
    """Creating a timer.

    - If it is created without defined count of shots, it is a periodic timer
      marked with "R" (repeating) in the string instance representation.
    - If it is created with count greater than 1, it is a countdown timer
      marked with "C" (countdown) in the string instance representation.
    - If it is created with count equal 1, it is an one-shot timer
      marked with "O" (oneshot) in the string instance representation.
    """

    _instances = 0     # Number of class instances

    def __init__(self, period=1, callback=None, *args, **kwargs):
        """Initialize instance object - constructor.

        Positional arguments:
        ---------------------
        period -- timer interval in seconds; default 1 sec
        callback -- function or tuple of them calling by the timer

        Keyworded arguments:
        --------------------
        count -- number of desired shots of the timer; default None for
                 periodic timer. It should be positive integer, otherwise it is
                 converted to this data type
        name -- name of the timer; default is class name

        - Remaining arguments are passed to the callback function.
        """
        self._logger = logging.getLogger(" ".join([__name__, __version__]))
        self._period = max(float(period), 0.0)
        self._callback = callback
        self._prescalers = []
        self._args = args
        self._kwargs = kwargs
        self._count = self._kwargs.pop("count", None)
        self._name = self._kwargs.pop("name", "{}"
                                      .format(self.__class__.__name__))
        type(self)._instances += 1
        self._order = type(self)._instances
        self._logger.debug("Instance of %s no. %d created",
                           self.__class__.__name__, self._order)
        self._timer = None
        self._stopping = False  # Flag about timer cancel request imposed
        self._repeate = True    # Flag about repeating timer
        # Mark timer
        if self._count is None:
            self._mark = "R"
        else:
            self._count = max(int(self._count), 0)
            if self._count > 1:
                self._mark = "C"
            elif self._count == 1:
                self._mark = "O"
                self._repeate = False   # Flag about on-shot timer

    def __del__(self):
        """Cleansing at instance object destroying - destructor."""
        self._logger.debug("Instance no.%d of %s deleted",
                           self._order, self.__class__.__name__)
        type(self)._instances -= 1

    def __str__(self):
        """Represent instance object as a string.

        All the relevant timer's parameters are involved in the string, i.e.,
        period, mark, and instance number.
        """
        return "{}({}s-{}{}-{})".format(
            self._name,
            float(self._period),
            self._mark,
            '' if self._count is None else str(self._count),
            self._order
        )

    def _create_timer(self):
        """Create new timer object and start it."""
        if not self._stopping:
            self._timer = threading.Timer(self._period, self._run_callback)
            self._timer.name = self._name
            self._timer.start()

    def _run_callback(self):
        """Run external instance callback.

        Injected keywarded arguments to callbacks:
        ------------------------------------------
        exec_last -- flag about last calling at countdown timers
        """
        if self._callback is None:
            return
        if self._count is not None:
            if self._count <= 0:
                return
            if self._count == 1:
                self._repeate = False
        try:
            # Call basic timer callback
            callbacks = self._callback
            if not isinstance(callbacks, tuple):
                callbacks = tuple([callbacks])
            for callback in callbacks:
                self._logger.debug(
                    "Main callback %s of %s launched",
                    callback.__name__, str(self)
                )
                callback(
                    *self._args,
                    exec_last=not self._repeate,
                    **self._kwargs
                )
            # Count down prescalers and call callbacks of expired ones
            for prescaler in self._prescalers:
                prescaler["counter"] -= 1
                if prescaler["counter"] <= 0:
                    prescaler["counter"] = prescaler["factor"]
                    callbacks = prescaler["callback"]
                    if not isinstance(callbacks, tuple):
                        callbacks = tuple([callbacks])
                    for callback in callbacks:
                        self._logger.debug(
                            "Prescaler %d callback %s of %s launched",
                            prescaler["factor"],
                            callback.__name__, str(self)
                        )
                        callback(
                            *prescaler["args"],
                            exec_last=not self._repeate,
                            **prescaler["kwargs"]
                        )
        except Exception:
            self._logger.error("Running callbacks of %s failed:",
                               str(self), exc_info=True)
        finally:
            if self._repeate:
                self._create_timer()
                if self._count is not None:
                    self._count -= 1

    def start(self):
        """Create timer thread object and store it in the instance."""
        if (self._count or 1) <= 0:
            self._logger.debug("%s not started", str(self))
            return
        else:
            self._logger.debug("%s started", str(self))
            self._create_timer()

    def stop(self):
        """Stop timer."""
        self._stopping = True
        if self._timer is not None:
            self._logger.debug("%s stopped", str(self))
            self._timer.cancel()

    def prescaler(self, factor, callback, *args, **kwargs):
        """Register a callback function called at each factor tickself.

        Positional arguments:
        ---------------------
        factor -- integer divider of the initial timer period. It is truncated
                  to integer and ignored if less than 2.
        callback -- function or tuple of them calling by the timer
                    at each factor-th period
        args -- additional positional arguments passed to the callback

        Keyworded arguments:
        --------------------
        kwargs -- additional keyworded arguments passed to the callback.

        - The prescaler method enables launching a specific callback
          at multiple timer period and acts as a frequency divider.
        - Prescale factor equal 1 is useless, because it is equivalent to basic
          timer callback. In this case it is ignored.
        - The prescaler method can be called multiple times. For the same
          factor the corresponding callback is updated including its arguments.
          If None, the prescaler is removed.
        - None of prescalers is launched if basic timer callback is defined or
          timer is one-timer one.
        - All prescalers are called at random order, but usually in order of
          their registration.
        """
        factor = int(factor)
        if factor < 2:
            return
        # Find existing prescaler and remove or update it
        new = True
        for i, prescaler in enumerate(self._prescalers):
            if prescaler["factor"] == factor:
                if callback is None:
                    self._prescalers.pop(i)
                else:
                    prescaler["callback"] = callback
                    prescaler["args"] = args
                    prescaler["kwargs"] = kwargs
                new = False
                break
        # Create new prescaler
        if new:
            prescaler = {
                "counter": factor,
                "factor": factor,
                "callback": callback,
                "args": args,
                "kwargs": kwargs,
            }
            self._prescalers.append(prescaler)

    def get_prescalers(self):
        """Return list of prescalers."""
        if hasattr(self, "_prescalers"):
            return self._prescalers
