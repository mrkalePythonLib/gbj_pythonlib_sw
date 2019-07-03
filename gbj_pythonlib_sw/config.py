# -*- coding: utf-8 -*-
"""Module for managing a configuration INI file."""
__version__ = '0.3.0'
__status__ = 'Testing'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2018, ' + __author__
__credits__ = []
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


import logging
try:
    import configparser
except Exception:
    from six.moves import configparser


###############################################################################
# Classes
###############################################################################
class Config(object):
    """Create a manager for a configuration INI file.

    Arguments
    ---------
    file : string, pointer
        Full path to a configuration file or file pointer of already opened
        file.
        *The argument is mandatory and has no default value.*

    Notes
    -----
    A single class instance object manages just one configuration file.
    If more configuration files are needed to manage, separate instances should
    be created.

    """

    def __init__(self, file):
        """Create the class instance - constructor."""
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug('Instance of %s created', self.__class__.__name__)
        self._parser = configparser.ConfigParser()
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
            return 'No object of type "{}"'.format(self.__class__.__name__)
        else:
            return 'Config file "{}"'.format(self._file)

    def option(self, option, section, default=None):
        """Read configuration option's value.

        Arguments
        ---------
        option : str
            Configuration file option to be read.
            *The argument is mandatory and has no default value.*
        section : str
            Configuration file section where to search the option.
            *The argument is mandatory and has no default value.*
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

    def option_split(self, option, section, appendix=[], separator=','):
        """Read configuration option, append to it, and split its value.

        Arguments
        ---------
        option : str
            Configuration file option to be read.
            *The argument is mandatory and has no default value.*
        section : str
            Configuration file section where to search the option.
            *The argument is mandatory and has no default value.*
        appendix : list
            List of additonal option value parts that should be added
            to the read option for splitting purposes.
        separator : str
            String used as a separator for spliting the option. It is used
            for glueing appendix list members with read option and at the same
            time for splitting the entire, composed option value.

        Returns
        -------
        list of str
            List of a configuration option parts.

        """
        # Read option
        value = self.option(option, section)
        if value is None:
            return value
        # Append list to option
        separator = str(separator or '')
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
            *The argument is mandatory and has no default value.*

        Returns
        -------
        list of str
            List of configuration option names.

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

        Returns
        -------
        str
            Content of the configuration file without comments.

        Notes
        -----
        All section and options are listed including from ``DEFAULT`` section.

        """
        pattern = '\n\n---CONGIGURATION - {}---'
        content = pattern.format('BOF')
        for section in self._parser.sections():
            content += '\n\n[{}]'.format(section)
            for name, value in self._parser.items(section):
                content += '\n{} = {}'.format(name, value)
        content += pattern.format('EOF')
        return content
