# -*- coding: utf-8 -*-
"""Module for managing and executing triggers as value dependend callbacks."""
__version__ = '0.3.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2018-2019, ' + __author__
__credits__ = []
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


import logging


###############################################################################
# Variables
###############################################################################
triggers = {}
"""dict: Registration storage of triggers."""


###############################################################################
# Functions
###############################################################################
def register(trigger):
    """Store a trigger object in the registration dictionary.

    Arguments
    ---------
    trigger : object
        Object of a trigger that is used as a value in triggers registration
        dictionary.
        - The ``name`` attribute of the object is used as a trigger name.
        - If name already exists in the dictionary, the trigger is updated.

    """
    if trigger is None or not isinstance(trigger, Trigger):
        return
    triggers[trigger.name] = trigger


def unregister(name):
    """Remove a trigger with provided name from the registration dictionary."""
    if name is None:
        return
    name = str(name)
    try:
        triggers.pop(name)
    except KeyError:
        pass


def run_all(value):
    """Run all registered triggers with comparison value."""
    for trigger in triggers:
        triggers[trigger].run(value)


###############################################################################
# Classes
###############################################################################
class Trigger(object):
    """Creating and registering a trigger.

    Arguments
    ---------
    threshold : float
        Mandatory threshold value, which in comparison to an provided value
        causes running a callback function(s).
    callback : function or tuple of functions
        Mandatory one or more functions in role of callbacks that the trigger
        calls when value crosses threshold.

    Keyword Arguments
    -----------------
    mode : str
        Processing mode of the trigger. The argument is defined by one of
        following class's constants
        - ``UPPER``: Callback is run in either case when execution
            of the trigger is called and provided comparison value reaches or
            exceeds the threshold.
        - ``UPPER1``: Callback is run at execution of the trigger only if
            provided comparison value reaches or exceeds
            the threshold while at previous execution it was bellow the
            threshold. So that the callback is run only once by exceeding
            threshold. In order to call it again, the comparison value should
            sink bellow the threshold at first.
        - ``LOWER``: Callback is run in either case when execution
            of the trigger is called and provided comparison value sinks
            to the threshold or bellow.
        - ``LOWER1``: Callback is run at execution of the trigger only if
            provided comparison value sinks to threshold or bellow while
            at previous execution it was over the threshold. So that the
            callback is run only once by sinking under the threshold. In order
            to call it again, the comparison value should exceed the threshold
            at first.
        Default mode is the first one in mentioned list of constants.
    name : str
        Name of the trigger incorporated to its object. If none is provided,
        the concatenation of its class name and order is used.

    See Also
    --------
    register_trigger : Registration of triggers.

    """

    MODE = ['UPPER', 'UPPER1', 'LOWER', 'LOWER1']
    """list of str: Available trigger types."""

    _instances = 0
    """int: Number of class instances."""

    def __init__(self, threshold, callback, *args, **kwargs):
        """Create the class instance - constructor."""
        type(self)._instances += 1
        self._args = args
        self._kwargs = kwargs
        #
        self.__threshold = abs(float(threshold))
        # Sanitize callbacks
        if not isinstance(callback, tuple):
            callback = tuple([callback])
        self._callbacks = callback
        # Sanitize name
        self._order = type(self)._instances
        self.__name = self._kwargs.pop('name',
            f'{self.__class__.__name__}{self._order}')
        # Sanitize mode
        self._mode = str(self._kwargs.pop('mode', self.MODE[0])).upper()
        if self._mode not in self.MODE:
            self._mode = self.MODE[0]
        # Register trigger
        self._value = None
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
        """Represent instance object as a string."""
        msg = \
            f'{self.name}(' \
            f'{float(self.__threshold)}-' \
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
            f'threshold={repr(self.__threshold)}, ' \
            f'callback={cb}, ' \
            f'name={repr(self.name)}, ' \
            f'args={repr(self._args)}, ' \
            f'kwargs={repr(self._kwargs)})'
        return msg

    @property
    def name(self):
        """Name of the trigger."""
        return self.__name

    @property
    def threshold(self):
        """Trigger threshold value."""
        return self.__threshold

    @threshold.setter
    def threshold(self, value):
        """Set trigger threshold value."""
        try:
            self.__threshold = abs(float(value))
        except ValueError:
            pass

    def _EXECUTE(func):
        """Decorate evaluation function of the trigger."""

        def _decorator(self, value):
            """Compare value and execute all trigger's callbacks if needed.

            Arguments
            ---------
            value : float
                Mandatory comparison value, which is compared to the threshold
                in order to run callback(s).
            ids : list
                List of trigger identifiers that should be evaluated.

                - If the input value is not a list, e.g., just string with
                identifier of one trigger or string with tuple of identifiers,
                it is converted to the list.
                - If argument is not provided, all triggers are executed against
                the comparison value.

            Other Parameters
            ----------------
            value : float
                Comparison value.
            threshold : float
                Threshold value taken from definition of respective trigger.

            Warning
            -------
            The method injects other parameters to each called callback function
            as keyword arguments in order to inform those callbacks about values,
            that caused their invocation.

            """
            runflag = func(self, value)
            self._value = value
            if runflag:
                for callback in self._callbacks:
                    msg = \
                        f"{self._mode} trigger's " \
                        f'callback {callback.__name__} ' \
                        f'for threshold {str(self.__threshold)} ' \
                        f'at value {str(value)}'
                    self._logger.debug(msg)
                    try:
                        callback(
                            *self._args,
                            value=value,
                            threshold=self.__threshold,
                            **self._kwargs
                        )
                    except Exception:
                        self._logger.error(
                            'Running callback %s failed:',
                            callback.__name__, exc_info=True)
            return runflag
        return _decorator

    @_EXECUTE
    def _run_upper(self, value):
        """Evaluate upper trigger."""
        return value >= self.__threshold

    @_EXECUTE
    def _run_upper1(self, value):
        """Evaluate one-time upper trigger."""
        return (self._value is None or self._value < self.__threshold) \
            and value >= self.__threshold

    @_EXECUTE
    def _run_lower(self, value):
        """Evaluate lower trigger."""
        return value <= self.__threshold

    @_EXECUTE
    def _run_lower1(self, value):
        """Evaluate one-time lower trigger."""
        return (self._value is None or self._value > self.__threshold) \
            and value <= self.__threshold

    def run(self, value):
        """Process trigger with comparison value."""
        func = eval('self._run_' + self._mode.lower())
        return func(value)


###############################################################################
# Trigger variants
###############################################################################
class TriggerUpper(Trigger):
    """Creating and registering an upper trigger."""

    def __init__(self, threshold, callback, *args, **kwargs):
        """Create the class instance - constructor."""
        kwargs.pop('mode', None)
        super().__init__(
            threshold,
            callback,
            *args,
            mode='UPPER',
            **kwargs,
        )
        
class TriggerUpper1(Trigger):
    """Creating and registering a one-time upper trigger."""

    def __init__(self, threshold, callback, *args, **kwargs):
        """Create the class instance - constructor."""
        kwargs.pop('mode', None)
        super().__init__(
            threshold,
            callback,
            *args,
            mode='UPPER1',
            **kwargs,
        )

class TriggerLower(Trigger):
    """Creating and registering a lower trigger."""

    def __init__(self, threshold, callback, *args, **kwargs):
        """Create the class instance - constructor."""
        kwargs.pop('mode', None)
        super().__init__(
            threshold,
            callback,
            *args,
            mode='LOWER',
            **kwargs,
        )

class TriggerLower1(Trigger):
    """Creating and registering a one-time lower trigger."""

    def __init__(self, threshold, callback, *args, **kwargs):
        """Create the class instance - constructor."""
        kwargs.pop('mode', None)
        super().__init__(
            threshold,
            callback,
            *args,
            mode='LOWER1',
            **kwargs,
        )
