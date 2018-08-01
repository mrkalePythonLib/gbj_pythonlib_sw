#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Module for statistical filtering."""
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
AVERAGE = 0
MEDIAN = 1
MINIMUM = 2
MAXIMUM = 3
STAT_TYPES = ['Average', 'Median', 'Minimum', 'Maximum']


###############################################################################
# Classes
###############################################################################
class StatFilter(object):
    """Creating a scuffolding for statistical filtering."""

    def __init__(self, value_max=None, value_min=None, buffer_len=5,
                 decimals=None):
        """Initialize instance object with common parameters.

        Positional arguments:
        ---------------------
        value_max -- maximal measuring value acceptable for filtering.
        value_min -- minimal measuring value acceptable for filtering.
        buffer_len -- number of values held in the data buffer used for
                      statistical filtering. It should be an odd number,
                      otherwise it is extended to the nearest odd one.
        decimals -- number of decimal places for rounding filtering results.
                    If None, no rounding occures.
        """
        self._logger = logging.getLogger(" ".join([__name__, __version__]))
        self._value_max = None
        self._value_min = None
        try:
            self._decimals = abs(int(decimals))
        except TypeError:
            self._decimals = None
        self._buffer = []
        self.set_filter(value_max=value_max, value_min=value_min)
        self.set_buffer(buffer_len)
        self.reset()

    def __del__(self):
        """Cleansing at instance object destroying - destructor."""

    def __str__(self):
        """Represent instance object as a string."""
        return "Data {}-{}[{}]".format(self._value_min or 'na',
                                       self._value_max or 'na',
                                       len(self._buffer))

    def reset(self):
        """Reset instance object to initial state."""
        self._buffer = [None] * len(self._buffer)

    def filter(self, value):
        """Filter value against acceptable value range.

        Positional arguments:
        ---------------------
        value -- value to be filtered. If outside the value range, None is
                 returned.
        """
        if value is None:
            return None
        if self._value_max is not None and value > self._value_max:
            self._logger.warning("Rejected value %f greater than %f",
                                 value, self._value_max)
            return None
        if self._value_min is not None and value < self._value_min:
            self._logger.warning("Rejected value %f less than %f",
                                 value, self._value_min)
            return None
        return value

    def result(self, value):
        """Return rounded value if needed and possible."""
        try:
            r = round(value, self._decimals)
        except TypeError:
            r = value
        self._logger.debug("Result %s rounded to %d decimal(s)",
                           r, self._decimals)
        return r

    # -------------------------------------------------------------------------
    # Setters
    # -------------------------------------------------------------------------
    def set_filter(self, **kwargs):
        """Set acceptable value range.

        Keyworded arguments:
        --------------------
        value_max -- maximal measuring value acceptable for filtering.
                     Default from constructor.
        value_min -- minimal measuring value acceptable for filtering.
                     Default from constructor.
        """
        self._value_max = kwargs.pop("value_max", self._value_max)
        self._value_min = kwargs.pop("value_min", self._value_min)

        if self._value_max is None or self._value_min is None:
            return

        if self._value_max < self._value_min:
            t = self._value_max
            self._value_max = self._value_min
            self._value_min = t

    def set_buffer(self, buffer_len=5):
        """Adjust data buffer for staticital filtering."""
        buffer_len = abs(buffer_len) | 1    # Make odd number and minimum 1
        if self.get_buffer_len() < buffer_len:
            for i in range(buffer_len - self.get_buffer_len()):
                self._buffer.append(None)
        elif self.get_buffer_len() > buffer_len:
            for i in range(self.get_buffer_len() - buffer_len):
                self._buffer.pop(i)

    # -------------------------------------------------------------------------
    # Getters
    # -------------------------------------------------------------------------
    def get_buffer_len(self):
        """Return real length of the data buffer.

        - Usually the returned value is the same as length put to the
          constructor.
        - If class has adjusted or limited the input buffer length, the
          method returns the actual length.
        - The method is useful, if the length has been put to the constructor
          as a numeric literal and there is no variable of the length to use
          it in other statements.
        """
        return len(self._buffer)

    def get_value_min(self):
        """Return minimal acceptable value."""
        return self._value_min

    def get_value_max(self):
        """Return maximal acceptable value."""
        return self._value_max

    def get_readings(self):
        """Return current number of values in data buffer.

        - The statistical calculation can be provided beforeregistering
          the full data buffer. In that case the method returns the values,
          which a statistic is calculated from.
        - Usually the returned value should be the same as length of the data
          buffer at the end of a measurement cycle.
        """
        for i, value in enumerate(self._buffer):
            if value is None:
                return i
        return self.get_buffer_len()


# -----------------------------------------------------------------------------
# Exponential filtering
# -----------------------------------------------------------------------------
class StatFilterExponential(StatFilter):
    """Exponential statistical filtering."""

    def __init__(self, factor=0.5, value_max=None, value_min=None,
                 decimals=None):
        """Initialize instance object with common parameters.

        Positional arguments:
        ---------------------
        factor -- smoothing factor for exponential filtering.
                  Default for running average.
                  Value range 0.0 ~ 1.0.
        value_max -- maximal measuring value acceptable for filtering.
        value_min -- minimal measuring value acceptable for filtering.
        decimals -- number of decimal places for rounding filtering results.
                    If None, no rounding occures.
        """
        self._factor = abs(factor)
        self._factor = min(self._factor, 1.0)
        self._factor = max(self._factor, 0.0)
        super(type(self), self).__init__(
            value_max,
            value_min,
            1,
            decimals,
        )
        self._logger.debug("Instance of %s created", self.__class__.__name__)
        self._logger.debug("Smoothing factor %.2f", self._factor)

    def result(self, value=None):
        """Calculate and return statistically smoothed value.

        Positional arguments:
        ---------------------
        value -- sample value to be filtered. If None, recent filtered result
                 provided.

        - The method calculates a new filtered value from the input value,
          previous stored filtered value, and stored smoothing factor in the
          class instance object.
        - The very first input value is considered as a previous filtered value
          or starting value.
        """
        value = self.filter(value)
        if value is not None:
            if self.get_readings():
                self._buffer[0] += self.get_factor()\
                                 * (value - self._buffer[0])
            else:
                self._buffer[0] = value
            self._logger.debug(
                "Value %s, Statistic %s",
                value, self._buffer[0]
            )
        return super(type(self), self).result(self._buffer[0])

    # -------------------------------------------------------------------------
    # Getters
    # -------------------------------------------------------------------------
    def get_factor(self):
        """Return smoothing factor."""
        if hasattr(self, "_factor"):
            return self._factor


# -----------------------------------------------------------------------------
# Running statistics filtering
# -----------------------------------------------------------------------------
class StatFilterRunning(StatFilter):
    """Running statistics filtering."""

    def __init__(self, stat_type=AVERAGE, value_max=None, value_min=None,
                 buffer_len=5, decimals=None):
        """Initialize instance object with common parameters.

        Positional arguments:
        ---------------------
        stat_type -- type of statistic calculated from registered running
                     values.
        value_max -- maximal measuring value acceptable for filtering.
        value_min -- minimal measuring value acceptable for filtering.
        buffer_len -- number of values held in the data buffer used for
                      statistical filtering. It should be an odd number,
                      otherwise it is extended to the nearest odd one.
        decimals -- number of decimal places for rounding filtering results.
                    If None, no rounding occurs.
        """
        self.set_stat_type(stat_type)
        super(type(self), self).__init__(
            value_max,
            value_min,
            buffer_len,
            decimals,
        )
        self._logger.debug("Instance of %s created", type(self).__name__)

    def _register_value(self, value):
        """Filter and register new value to the data buffer.

        Positional arguments:
        ---------------------
        value -- sample value to be filtered.

        - The most recent (fresh) sample value is always in the 0 index of the
          data buffer.
        - If new value does not fit to the filter range, it is ignored.
        - Sample values are shifted to the right in the data buffer (to higher
          indices), so that the most recent value is lost. The new value is
          stored in the zero index of  the buffer.
        """
        value = self.filter(value)
        if value is not None:
            # Shift if any real value is stored
            if self.get_readings():
                for i in range(self.get_buffer_len() - 1, 0, -1):
                    self._buffer[i] = self._buffer[i - 1]
            # Storing just real value
            self._buffer[0] = value
        return value

    def result_avg(self, value=None):
        """Register new value and calculate running average.

        Positional arguments:
        ---------------------
        value -- new sample value. If None, statistic is calculated from
                 current content of the data buffer.

        - The method calculates new statistic from the input value and
          previous stored sample values in the class instance object.
        """
        statistic = self._register_value(value)
        readings = self.get_readings()
        if readings:
            statistic = 0
            for i in range(readings):
                statistic += self._buffer[i]
            statistic /= readings
        return super(type(self), self).result(statistic)

    def result_med(self, value=None):
        """Register new value and calculate running median.

        Positional arguments:
        ---------------------
        value -- new sample value. If None, statistic is calculated from
                 current content of the data buffer.

        - The method calculates new statistic from the input value and
          previous stored sample values in the class instance object.
        - Until the data buffer is full, the method calculates median high at
          even readings in the buffer.
        """
        statistic = self._register_value(value)
        readings = self.get_readings()
        if readings:
            statistic = self._buffer[readings // 2]
        return super(type(self), self).result(statistic)

    def result_min(self, value=None):
        """Register new value and calculate running minimum.

        Positional arguments:
        ---------------------
        value -- new sample value. If None, statistic is calculated from
                 current content of the data buffer.

        - The method calculates new statistic from the input value and
          previous stored sample values in the class instance object.
        """
        statistic = self._register_value(value)
        readings = self.get_readings()
        if readings:
            statistic = self._buffer[0]
            for i in range(1, readings):
                statistic = min(statistic, self._buffer[i])
        return super(type(self), self).result(statistic)

    def result_max(self, value=None):
        """Register new value and calculate running maximum.

        Positional arguments:
        ---------------------
        value -- new sample value. If None, statistic is calculated from
                 current content of the data buffer.

        - The method calculates new statistic from the input value and
          previous stored sample values in the class instance object.
        """
        statistic = self._register_value(value)
        readings = self.get_readings()
        if readings:
            statistic = self._buffer[0]
            for i in range(1, readings):
                statistic = max(statistic, self._buffer[i])
        return super(type(self), self).result(statistic)

    def result(self, value=None):
        """Register new value and calculate default running statistic.

        Positional arguments:
        ---------------------
        value -- new sample value. If None, statistic is calculated from
                 current content of the data buffer.

        - The method calculates a new filtered value from the input value and
          previous stored sample values in the class instance object.
        """
        self._logger.debug("Default statistic: %s",
                           STAT_TYPES[self.get_stat_type()])
        if self._stat_type == AVERAGE:
            return self.result_avg(value)
        elif self._stat_type == MEDIAN:
            return self.result_med(value)
        elif self._stat_type == MINIMUM:
            return self.result_min(value)
        elif self._stat_type == MAXIMUM:
            return self.result_max(value)
        else:
            return None

    # -------------------------------------------------------------------------
    # Setters
    # -------------------------------------------------------------------------
    def set_stat_type(self, stat_type):
        """Set running statistics type as a default for resulting.

        Positional arguments:
        ---------------------
        stat_type -- type of a statistic calculated from registered running
                     values by default in the method 'result'. If not from
                     allowed enumeration, nothing changes.
        """
        if stat_type in [
            AVERAGE,
            MEDIAN,
            MINIMUM,
            MAXIMUM,
        ]:
            self._stat_type = stat_type

    # -------------------------------------------------------------------------
    # Getters
    # -------------------------------------------------------------------------
    def get_stat_type(self):
        """Return defaulting running statistics type."""
        if hasattr(self, "_stat_type"):
            return self._stat_type
