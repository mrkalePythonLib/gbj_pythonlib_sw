#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Module for managing and executing triggers - value dependend callbacks."""
__version__ = "0.1.0"
__status__ = "Development"
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
LOWER = 1


###############################################################################
# Classes
###############################################################################
class Trigger(object):
    """Creating a trigger manager."""

    def __init__(self):
        """Initialize instance object - constructor."""
        self._logger = logging.getLogger(" ".join([__name__, __version__]))
        self._logger.debug("Instance of %s created", self.__class__.__name__)
        self.del_triggers()

    def __str__(self):
        """Represent instance object as a string."""
        return "Triggers {}".format(len(self._triggers))

    def set_trigger(self, id, mode=None, value=None, callback=None,
                    *args, **kwargs):
        """Create or update trigger.

        Positional arguments:
        ---------------------
        id -- unique identifier of a trigger in the list of them of any type
        mode -- processing mode of the trigger [UPPER, LOWER]
        value -- threshold value
        callback -- function or tuple of them calling at threshold value.
        args -- additional positional arguments passed to the callback after
                forced arguments by this class.

        Keyworded arguments:
        --------------------
        kwargs -- additional keyworded arguments passed to the callback.

        Returns:
        --------
        Exception NameError - if identifier is not provided
        Exception TypeError - if mode is not from the allowed enumeration

        - The trigger method can be called multiple times. For the same
          trigger value corresponding callback is updated including its
          arguments. If None, the trigger is removed.
        - For a particular threshold value only one trigger can be defined,
          either upper or lower, but not both.

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
        """Return list of triggers."""
        return self._triggers

    def exec_triggers(self, value, ids=[]):
        """Evaluate and execute all or listed triggers.

        Positional arguments:
        ---------------------
        value -- comparison value
        ids -- list of trigger identifiers that should be evaluated

        Injected keyworded arguments to callbacks:
        ------------------------------------------
        value -- comparison value
        threshold -- threshold value
        """
        # Sanitize arguments
        if ids is not None and not isinstance(ids, list):
            ids = list(ids)
        if len(ids) == 0:
            ids = None
        # Evaluate listed or all triggers
        for trigger in self._triggers:
            # Detect not listed trigger
            if trigger["id"] not in (ids or []):
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

        Positional arguments:
        ---------------------
        ids -- list of trigger identifiers that should be Removed
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
