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
        self.value_max = value_max
        self.value_min = value_min
        #
        self._buffer = []
        self.buffer_len = buffer_len
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
            f'value_max={repr(self.value_max)}, ' \
            f'value_min={repr(self.value_min)}, ' \
            f'buffer_len={repr(self.buffer_len)})'
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
            if self.readings:
                for i in range(self.buffer_len - 1, 0, -1):
                    self._buffer[i] = self._buffer[i - 1]
            # Storing just real value
            self._buffer[0] = value
        return value

    def reset(self):
        """Reset instance object to initial state."""
        self._buffer = [None] * self.buffer_len

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
        if self.value_max is not None and value > self.value_max:
            self._logger.warning('Rejected value %f greater than %f',
                                 value, self.value_max)
            return
        if self.value_min is not None and value < self.value_min:
            self._logger.warning('Rejected value %f less than %f',
                                 value, self.value_min)
            return
        return value

    @property
    def buffer_len(self):
        """Real length of the data buffer.

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

    @buffer_len.setter
    def buffer_len(self, value=BUFFER_LEN_DEF):
        """Adjust data buffer length for statistical smoothing."""
        try:
            # Make odd number and minimum 1
            buffer_len = abs(int(value)) | 1
        except ValueError:
            return
        if self.buffer_len < buffer_len:
            self._buffer.extend([None] * (buffer_len - self.buffer_len))
        elif self.buffer_len > buffer_len:
            for i in range(self.buffer_len - buffer_len):
                self._buffer.pop(i)

    @property
    def value_min(self):
        """Minimal acceptable value."""
        return self._value_min

    @value_min.setter
    def value_min(self, value):
        """Set minimal acceptable value."""
        if value is None:
            self._value_min = None
            return
        try:
            self._value_min = float(value)
        except ValueError:
            pass

    @property
    def value_max(self):
        """Maximal acceptable value."""
        return self._value_max

    @value_max.setter
    def value_max(self, value):
        """Set maximal acceptable value."""
        if value is None:
            self._value_max = None
            return
        try:
            self._value_max = float(value)
        except ValueError:
            pass

    @property
    def readings(self):
        """Current number of values in data buffer.

        Notes
        -----
        - The statistical calculation can be provided before filling
          the entire data buffer. In that case the method returns the values
          count, which a statistic is calculated from.
        - Usually the returned value should be the same as length of the data
          buffer at the end of a measurement cycle.

        """
        return len([i for i in self._buffer if i is not None])


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
        self.factor = factor
        super().__init__(
            value_max,
            value_min,
            1
        )

    def __str__(self):
        """Represent instance object as a string."""
        msg = \
            f'ExpFilter(' \
            f'{self.factor}/' \
            f'{self.value_min}~' \
            f'{self.value_max})'
        return msg

    def __repr__(self):
        """Represent instance object officially."""
        msg = \
            f'{self.__class__.__name__}(' \
            f'factor={repr(self.factor)}, ' \
            f'value_max={repr(self.value_max)}, ' \
            f'value_min={repr(self.value_min)})'
        return msg

    @property
    def factor(self):
        """Current float smoothing factor."""
        return self._factor

    @factor.setter
    def factor(self, value):
        """Set current float smoothing factor."""
        try:
            self._factor = float(value or self.FACTOR_DEF)
        except TypeError:
            self._factor = self.FACTOR_DEF
        self._factor = max(min(abs(self._factor),
                               self.FACTOR_MAX), self.FACTOR_MIN)

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
            if self.readings:
                self._buffer[0] += self.factor * (value - self._buffer[0])
            else:
                self._buffer[0] = value
            self._logger.debug(
                'Value %s, Statistic %s',
                value, self._buffer[0]
            )
        return self._buffer[0]


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
    def_stat : str
        Default available statistic type for general result from the list
        'AVG', 'MED', 'MAX', 'MIN'.

    """

    STAT_TYPE = ['AVG', 'MED', 'MAX', 'MIN']
    """list of str: Available statistical types."""

    def __init__(self,
                 value_max=None,
                 value_min=None,
                 buffer_len=BUFFER_LEN_DEF,
                 def_stat=STAT_TYPE[0],
                 ):
        self.stat_type = def_stat
        super().__init__(
            value_max,
            value_min,
            buffer_len,
        )

    def __str__(self):
        """Represent instance object as a string."""
        msg = \
            f'RunFilter(' \
            f'{self.stat_type}-' \
            f'{self.buffer_len}/' \
            f'{self.value_min}~' \
            f'{self.value_max})'
        return msg

    @property
    def stat_type(self):
        """Default statistic type for general result."""
        return self._def_stat

    @stat_type.setter
    def stat_type(self, def_stat=STAT_TYPE[0]):
        """Set default statistic type for general result.

        Arguments
        ---------
        def_stat : str
            Enumerated abbreviation from available statistic types.
            If unknown one provided, the default one is set.

        """
        def_stat = str(def_stat).upper()
        if def_stat not in self.STAT_TYPE:
            def_stat = self.STAT_TYPE[0]
        self._def_stat = def_stat

    def _REGISTER(func):
        """Decorate statistical function by registering its value."""

        def _decorator(self, value):
            value = self._register(value)
            if self.readings:
                result = func(self, value)
            if value is not None:
                self._logger.debug(
                    'Value %s, Statistic %s',
                    value, result
                )
            return result
        return _decorator

    @_REGISTER
    def result_min(self, value=None):
        """Calculate minimum from data buffer."""
        return min([i for i in self._buffer if i is not None])

    @_REGISTER
    def result_max(self, value=None):
        """Calculate maximum from data buffer."""
        return max([i for i in self._buffer if i is not None])

    @_REGISTER
    def result_avg(self, value=None):
        """Calculate mean from data buffer."""
        l = [i for i in self._buffer if i is not None]
        if len(l):
            return sum(l) / len(l)

    @_REGISTER
    def result_med(self, value=None):
        """Calculate median from data buffer."""
        l = self.get_readings()
        if l:
            return self._buffer[l // 2]

    def result(self, value=None):
        """Calculate default statistic from data buffer."""
        func = eval('self.result_' + self._def_stat.lower())
        return func(value)
