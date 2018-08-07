#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Module for managing and executing triggers as value dependend callbacks."""
__version__ = "0.2.0"
__status__ = "Testing"
__author__ = "Libor Gabaj"
__copyright__ = "Copyright 2018, " + __author__
__credits__ = []
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "libor.gabaj@gmail.com"


import logging


###############################################################################
# Constants
###############################################################################
UPPER = 0
"""int: Enumeration for upper trigger mode."""

LOWER = 1
"""int: Enumeration for lower trigger mode."""


###############################################################################
# Classes
###############################################################################
class Trigger(object):
    """Creating a trigger manager."""

    def __init__(self):
        """Create the class instance - constructor."""
        self._logger = logging.getLogger(" ".join([__name__, __version__]))
        self._logger.debug("Instance of %s created", self.__class__.__name__)
        self.del_triggers()

    def __str__(self):
        """Represent instance object as a string."""
        return "Triggers {}".format(len(self._triggers))

    def set_trigger(self, id, mode=None, value=None, callback=None,
                    *args, **kwargs):
        """Create or update trigger and register it to class instance.

        Arguments
        ---------
        id
            Unique identifier of a trigger in the list of them of any type.
            *The argument is mandatory and has no default value.*
        mode : enum
            Processing mode of the trigger. The argument is defined by one of
            module's constants ``UPPER``, ``LOWER``.

            - Upper trigger calls callback(s) when comparison value reaches or
              exceeds the threshold value.
            - Lower trigger calls callback(s) when comparison value sinks to
              the threshold value or below.

        value : float
            Threshold value, which in comparison to an comparison value causes
            running a callback function.
        callback : function, tuple of functions
            One of more functions in role of callbacks that the trigger calls
            when threshold value is reached from direction corresponding to the
            mode of the trigger.
        args : tuple
            Additional positional arguments passed to the callback(s) after
            forced arguments by this class.

        Keyword Arguments
        -----------------
        kwargs : dict
            Additional keyworded arguments passed to the callback(s).

        Raises
        ------
        NameError
            Identifier is not provided.
        TypeError
            Mode is not from the expected enumeration.

        Notes
        -----
        - The trigger method can be called multiple times.
        - For the same trigger identifier corresponding callback is updated
          including its arguments.

        """
        def mode_str(mod):
            return "upper" if mode == UPPER else "lower"

        # Sanitize arguments
        if id is None:
            errmsg = "No id provided"
            self._logger.error(errmsg)
            raise NameError(errmsg)
        if mode is not None and mode not in [UPPER, LOWER]:
            errmsg = "Unknown mode {}".format(mode)
            self._logger.error(errmsg)
            raise TypeError(errmsg)
        debug_str = " %s trigger %s with callback %s for value %s"
        # Update trigger
        new = True
        for i, trigger in enumerate(self._triggers):
            if trigger["id"] == id:
                trigger["callback"] = callback or trigger["callback"]
                trigger["value"] = value or trigger["value"]
                trigger["mode"] = mode or trigger["mode"]
                trigger["args"] = args or trigger["args"]
                trigger["kwargs"] = kwargs or trigger["kwargs"]
                self._triggers[i] = trigger
                self._logger.debug(
                    "Updated" + debug_str, mode_str(trigger["mode"]), id,
                    trigger["callback"].__name__, trigger["value"])
                new = False
                break
        # Create new trigger
        if new:
            trigger = {
                "id": id,
                "value": value,
                "callback": callback,
                "mode": mode,
                "args": args,
                "kwargs": kwargs,
            }
            self._triggers.append(trigger)
            self._logger.debug(
                "Created" + debug_str, mode_str(mode), id,
                callback.__name__, value)

    def get_triggers(self):
        """Return list of triggers.

        Returns
        -------
        list
            Registered triggers with all their parameters.

        """
        return self._triggers

    def exec_triggers(self, value, ids=[]):
        """Evaluate and execute all or listed triggers.

        Arguments
        ---------
        value : float
            Comparison value, which is compared to threshold values of triggers
            in order to run callback(s) or not.
            *The argument is mandatory and has no default value.*
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
        that caused  their invocation.

        """
        # Sanitize arguments
        if ids is not None and not isinstance(ids, list):
            ids = list(ids)
        if len(ids) == 0:
            ids = None
        # Evaluate listed or all triggers
        for trigger in self._triggers:
            # Detect not listed trigger
            if ids is not None and trigger["id"] not in ids:
                continue
            if (trigger["mode"] == UPPER and value > trigger["value"]) \
               or (trigger["mode"] == LOWER and value < trigger["value"]):
                    callbacks = trigger["callback"]
                    if not isinstance(callbacks, tuple):
                        callbacks = tuple([callbacks])
                    for callback in callbacks:
                        self._logger.debug(
                            "%s trigger callback %s for threshold value %f"
                            + " at current value %f",
                            "Upper" if trigger["mode"] == UPPER else "Lower",
                            callback.__name__,
                            trigger["value"],
                            value
                        )
                        callback(
                            *trigger["args"],
                            value=value,
                            threshold=trigger["value"],
                            **trigger["kwargs"]
                        )

    def del_triggers(self, ids=[]):
        """Delete all or listed triggers.

        Arguments
        ---------
        ids : list
            List of trigger identifiers that should be removed from class
            instance regristration.

        """
        # Sanitize arguments
        if ids is not None and not isinstance(ids, list):
            ids = list(ids)
        # Remove all triggers
        if ids is None or len(ids) == 0:
            self._triggers = []
            return
        # Remove listed triggers
        for i, trigger in enumerate(self._triggers):
            if trigger["id"] in ids:
                self._triggers.pop(i)
                self._logger.debug("Removed trigger %s", trigger["id"])
