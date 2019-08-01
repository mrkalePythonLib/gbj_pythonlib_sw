# -*- coding: utf-8 -*-
"""Module for statistical filtering and smoothing."""
__version__ = '0.4.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2018-2019, ' + __author__
__credits__ = []
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


import logging


###############################################################################
# Constants
###############################################################################
BUFFER_LEN_DEF = 5
"""int: Default buffer length."""


###############################################################################
# Classes
###############################################################################
class StatFilter(object):
    """Common statistical filtering and smoothing management.

    Arguments
    ---------
    value_max : float
        Maximal measuring value acceptable for filtering.
    value_min : float
        Minimal measuring value acceptable for filtering.
    buffer_len : int
        Positive integer number of values held in the data buffer used for
        statistical smoothing. It should be an odd number, otherwise it is
        extended to the nearest odd one.

    Notes
    -----
    This class should not be instanciated. It servers as a abstract class and
    a parent class for operational classes with corresponding statictical and
    smoothing methods.

    """

    def __init__(self,
                 value_max=None,
                 value_min=None,
                 buffer_len=BUFFER_LEN_DEF,
                 ):
        """Create the class instance - constructor."""
        self._value_max = None
        self._value_min = None
        self.set_filter(value_max=value_max, value_min=value_min)
        #
        self._buffer = []
        self.set_buffer(buffer_len)
        #
        self.reset()
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug(
            'Instance of %s created: %s',
            self.__class__.__name__, str(self)
        )

    def __repr__(self):
        """Represent instance object officially."""
        msg = \
            f'{self.__class__.__name__}(' \
            f'value_max={repr(self.get_value_max())}, ' \
            f'value_min={repr(self.get_value_min())}, ' \
            f'buffer_len={repr(self.get_buffer_len())})'
        return msg

    def _register(self, value):
        """Filter and register new value to the data buffer.

        Arguments
        ---------
        value : float
            Sample value to be registered in the data buffer and use for
            statistical smoothing if succesfully filtered.
            *The argument is mandatory and has no default value.*

        Notes
        -----
        - If new value does not fit to the filter range, it is ignored.
        - The most recent (fresh) sample value is always in the 0 index of the
          data buffer.
        - Sample values are shifted to the right in the data buffer (to higher
          indices), so that the most recent value is lost.

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

    def reset(self):
        """Reset instance object to initial state."""
        self._buffer = [None] * self.get_buffer_len()

    def filter(self, value):
        """Filter value against acceptable value range.

        Arguments
        ---------
        value : float
            Value to be filtered.
            *The argument is mandatory and has no default value.*

        Returns
        -------
        float
            If the input value is outside of the acceptable value range, None
            is returned, otherwise that value.

        """
        if value is None:
            return
        if self.get_value_max() is not None and value > self.get_value_max():
            self._logger.warning('Rejected value %f greater than %f',
                                 value, self.get_value_max())
            return
        if self.get_value_min() is not None and value < self.get_value_min():
            self._logger.warning('Rejected value %f less than %f',
                                 value, self.get_value_min())
            return
        return value

    #--------------------------------------------------------------------------
    # Setters
    #--------------------------------------------------------------------------
    def set_filter(self, **kwargs):
        """Set acceptable value range.

        Keyword arguments
        -----------------
        value_max : float
            Maximal measuring value acceptable for filtering.
        value_min : float
            Minimal measuring value acceptable for filtering.

        Notes
        -----
        - Initial (default) values are defined by the constructor.
        - Use just that argument, which you need to changing.

        """
        self._value_max = kwargs.pop('value_max', self.get_value_max())
        self._value_min = kwargs.pop('value_min', self.get_value_min())

        if self.get_value_max() is None or self._value_min is None:
            return

        if self.get_value_max() < self.get_value_min():
            self._value_max, self._value_min \
            = self.get_value_min(), self.get_value_max()

    def set_buffer(self, buffer_len=BUFFER_LEN_DEF):
        """Adjust data buffer length for statistical smoothing."""
        try:
            # Make odd number and minimum 1
            buffer_len = abs(int(buffer_len)) | 1
        except ValueError:
            return
        if self.get_buffer_len() < buffer_len:
            self._buffer.extend([None] * (buffer_len - self.get_buffer_len()))
        elif self.get_buffer_len() > buffer_len:
            for i in range(self.get_buffer_len() - buffer_len):
                self._buffer.pop(i)

    #--------------------------------------------------------------------------
    # Getters
    #--------------------------------------------------------------------------
    def get_buffer_len(self):
        """Return real length of the data buffer.

        Returns
        -------
        int
            Real utilized data buffer length.

        Notes
        -----
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
        """Return minimal acceptable value.

        Returns
        -------
        float
            Current acceptable minimal value for statistical smoothing.

        """
        return self._value_min

    def get_value_max(self):
        """Return maximal acceptable value.

        Returns
        -------
        float
            Current acceptable maximal value for statistical smoothing.

        """
        return self._value_max

    def get_readings(self):
        """Return current number of values in data buffer.

        Returns
        -------
        int
            Number of values acctually present in the data buffer.

        Notes
        -----
        - The statistical calculation can be provided before filling
          the entire data buffer. In that case the method returns the values
          count, which a statistic is calculated from.
        - Usually the returned value should be the same as length of the data
          buffer at the end of a measurement cycle.

        """
        for i, value in enumerate(self._buffer):
            if value is None:
                return i
        return self.get_buffer_len()


###############################################################################
# Exponential filtering
###############################################################################
class StatFilterExponential(StatFilter):
    """Exponential statistical smoothing.

    Arguments
    ---------
    factor : float
        Positive smoothing factor for exponential filtering.
        It is converted to absolute value provided.

        - Acceptable value range is ``0.0 ~ 1.0`` and input value is limited
          to it.
        - Default value ``0.5`` means ``running average``.
        - Value ``1.0`` means ``no smoothing``.

    value_max : float
        Maximal measuring value acceptable for filtering.
    value_min : float
        Minimal measuring value acceptable for filtering.

    """

    FACTOR_DEF = 0.5
    FACTOR_MIN = 0.0
    FACTOR_MAX = 1.0

    def __init__(self,
                 factor=FACTOR_DEF,
                 value_max=None,
                 value_min=None,
                 ):
        """Create the class instance - constructor."""
        try:
            self._factor = float(factor or self.FACTOR_DEF)
        except TypeError:
            self._factor = FACTOR_DEF
        self._factor = max(min(abs(self._factor),
                        self.FACTOR_MAX), self.FACTOR_MIN)
        super().__init__(
            value_max,
            value_min,
            1
        )
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug('Instance of %s created: %s',
            self.__class__.__name__, str(self)
            )

    def __str__(self):
        """Represent instance object as a string."""
        msg = \
            f'Exponential filter with factor ' \
            f'{repr(self.get_factor())} for data range ' \
            f'{repr(self.get_value_min())} ~ ' \
            f'{repr(self.get_value_max())}'
        return msg

    def __repr__(self):
        """Represent instance object officially."""
        msg = \
            f'{self.__class__.__name__}(' \
            f'factor={repr(self.get_factor())}, ' \
            f'value_max={repr(self.get_value_max())}, ' \
            f'value_min={repr(self.get_value_min())})'
        return msg

    def result(self, value=None):
        """Calculate statistically smoothed value.

        Arguments
        ---------
        value : float
            Sample value to be filtered.

        Returns
        -------
        float
            If None input value is provided, recent result is returned,
            otherwise the new smoothed value is.

        Notes
        -----
        - The method calculates a new filtered value from the input value,
          previous stored filtered value, and stored smoothing factor in the
          class instance object.
        - The very first input value is considered as a previous filtered value
          or starting value.

        """
        value = self.filter(value)
        if value is not None:
            if self.get_readings():
                self._buffer[0] += self.get_factor() \
                                 * (value - self._buffer[0])
            else:
                self._buffer[0] = value
            self._logger.debug(
                'Value %s, Statistic %s',
                value, self._buffer[0]
            )
        return self._buffer[0]

    #--------------------------------------------------------------------------
    # Getters
    #--------------------------------------------------------------------------
    def get_factor(self):
        """Return current smoothing factor.

        Returns
        -------
        float
            Current smoothing factor utilized for statistical smoothing.

        """
        return self._factor


###############################################################################
# Running statistics filtering
###############################################################################
class StatFilterRunning(StatFilter):
    """Running statistical smoothing.

    Arguments
    ---------
    value_max : float
        Maximal measuring value acceptable for filtering.
    value_min : float
        Minimal measuring value acceptable for filtering.
    buffer_len : int
        Positive integer number of values held in the data buffer used for
        statistical smoothing. It should be an odd number, otherwise it is
        extended to the nearest odd one.

    """

    def __str__(self):
        """Represent instance object as a string."""
        msg = \
            f'Running filter for data range ' \
            f'{repr(self.get_value_min())} ~ ' \
            f'{repr(self.get_value_max())} over ' \
            f'{repr(self.get_buffer_len())} samples'
        return msg

    def result_avg(self, value=None):
        """Register new value and calculate running average.

        Arguments
        ---------
        value : float
            New sample value. If None is provided, statistic is calculated from
            current content of the data buffer.

        Notes
        -----
        The method calculates new statistic from the input value and previously
        stored sample values in the class instance object.

        """
        statistic = self._register(value)
        readings = self.get_readings()
        if readings:
            statistic = 0
            for i in range(readings):
                statistic += self._buffer[i]
            statistic /= readings
        return statistic

    def result_med(self, value=None):
        """Register new value and calculate running median.

        Arguments
        ---------
        value : float
            New sample value. If None is provided, statistic is calculated from
            current content of the data buffer.

        Notes
        -----
        - The method calculates new statistic from the input value and
          previously stored sample values in the class instance object.
        - Until the data buffer is full, the method calculates high median
          at even readings in the buffer.

        """
        statistic = self._register(value)
        readings = self.get_readings()
        if readings:
            statistic = self._buffer[readings // 2]
        return statistic

    def result_min(self, value=None):
        """Register new value and calculate running minimum.

        Arguments
        ---------
        value : float
            New sample value. If None is provided, statistic is calculated from
            current content of the data buffer.

        Notes
        -----
        The method calculates new statistic from the input value and previously
        stored sample values in the class instance object.

        """
        statistic = self._register(value)
        readings = self.get_readings()
        if readings:
            statistic = self._buffer[0]
            for i in range(1, readings):
                statistic = min(statistic, self._buffer[i])
        return statistic

    def result_max(self, value=None):
        """Register new value and calculate running maximum.

        Arguments
        ---------
        value : float
            New sample value. If None is provided, statistic is calculated from
            current content of the data buffer.

        Notes
        -----
        The method calculates new statistic from the input value and previously
        stored sample values in the class instance object.

        """
        statistic = self._register(value)
        readings = self.get_readings()
        if readings:
            statistic = self._buffer[0]
            for i in range(1, readings):
                statistic = max(statistic, self._buffer[i])
        return statistic
