#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for managing a configuration file."""
__version__ = "0.4.1"
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
    """Create a manager for a configuration INI file.

    A single class instance object manages just one configuration file.
    If more configuration files are needed to manage, separate instance should
    be created.

    Arguments
    ---------
    file : string, pointer
        Full path to a configuration file or file pointer already opened
        file.

    """

    def __init__(self, file):
        """Create class instance."""
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

        Arguments
        ---------
        option : str
            Configuration file option to be read.
        section : str
            Configuration file section to be read from.
        default : str
            Default option value, if configuration file has neither
            the option nor the section.

        Returns
        -------
        str
            Configuration option value or default one.

        """
        if not self._parser.has_option(section, option):
            return default
        return self._parser.get(section, option) or default

    def option_split(self, option, section, appendix=[], separator=","):
        """Read configuration option and append and split its value to tuple.

        Arguments
        ---------
        option -- configuration file option to be read.
        section -- configuration file section to be read from.
        appendix -- list of additonal option value parts that should be added.
        separator -- string for separating appendix list members and split
                     the entire option value

        Returns
        -------
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
        """Read list of options in a section.

        Arguments
        ---------
        section : str
            Configuration section to be read from.

        Returns
        -------
        list of str
            List with configuration option names.

        """
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
        """Create string with configuration parameters in form of INI file.

        All section and options are listed including from DEFAULT section.

        Returns
        -------
        str
            Concent of configuration file without comments.

        """
        pattern = "\n\n---CONGIGURATION - {}---"
        content = pattern.format("BOF")
        for section in self._parser.sections():
            content += "\n\n[{}]".format(section)
            for name, value in self._parser.items(section):
                content += "\n{} = {}".format(name, value)
        content += pattern.format("EOF")
        return content
