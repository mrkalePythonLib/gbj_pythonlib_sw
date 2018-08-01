#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for managing a configuration file."""
__version__ = "0.4.0"
__status__ = "Development"
__author__ = "Libor Gabaj"
__copyright__ = "Copyright 2018, " + __author__
__credits__ = []
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "libor.gabaj@gmail.com"


# Standard library modules
import logging
from ConfigParser import SafeConfigParser


###############################################################################
# Classes
###############################################################################
class Config(object):
    """Creating a configuration manager object."""

    def __init__(self, file):
        """Initialize class instance.

        Positional arguments:
        ---------------------
        parameter file (string, pointer): full path to a configuration file.
        """
        self._logger = logging.getLogger(" ".join([__name__, __version__]))
        self._logger.debug("Instance of %s created", self.__class__.__name__)
        self._parser = SafeConfigParser()
        self._file = None

        if isinstance(file, str):
            self._file = file
            self._parser.read(file)
        else:
            self._parser.readfp(file)
            self._file = file.name

    def __str__(self):
        """Represent instance object as a string."""
        if self._file is None:
            return "No object of type '{}'".format(self.__class__.__name__)
        else:
            return "Config file '{}'".format(self._file)

    def option(self, option, section, default=None):
        """Read configuration option's value.

        Positional arguments:
        ---------------------
        option -- configuration file option to be read.
        section -- configuration file section to be read from.
        default -- default option value, if configuration file has neither
                   the option nor the section.

        Returns:
        --------
        Configuration option value or default one.

        """
        if not self._parser.has_option(section, option):
            return default
        return self._parser.get(section, option) or default

    def option_split(self, option, section, appendix=[], separator=","):
        """Read configuration option and append and split its value to tuple.

        Positional arguments:
        ---------------------
        option -- configuration file option to be read.
        section -- configuration file section to be read from.
        appendix -- list of additonal option value parts that should be added.
        separator -- string for separating appendix list members and split
                     the entire option value

        Returns:
        --------
        List with configuration option parts.

        """
        # Read option
        value = self.option(option, section)
        if value is None:
            return value
        # Append list to option
        separator = str(separator or "")
        if not isinstance(appendix, list):
            tmp = appendix
            appendix = []
            appendix.append(tmp)
        for suffix in appendix:
            value += separator + str(suffix)
        # Split, sanitize and list option parts
        result = []
        if separator:
            for part in value.split(separator):
                result.append(part.strip())
        else:
            result.append(value)
        return result

    def options(self, section):
        """Read list of configuration options in a section."""
        options = []
        for config_key in self._parser.options(section):
            if config_key in self._parser.defaults():
                continue
            options.append(config_key)
        return options

    # -------------------------------------------------------------------------
    # Getters
    # -------------------------------------------------------------------------
    def get_content(self):
        """Create string with configuration parameters in form of INI file."""
        pattern = "\n\n---CONGIGURATION - {}---"
        content = pattern.format("BOF")
        for section in self._parser.sections():
            content += "\n\n[{}]".format(section)
            for name, value in self._parser.items(section):
                content += "\n{} = {}".format(name, value)
        content += pattern.format("EOF")
        return content
