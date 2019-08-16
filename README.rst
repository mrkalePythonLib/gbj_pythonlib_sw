**********************
Purpose of the package
**********************


The package ``gbj_pythonlib_sw`` contains a set of Python modules for
supporting ordinary python console applications and scripts. Those module are
utilized as libraries.

- The documentation configuration for the package is located in the folder
  `docs/source`. The documentation in HTML format can be generated
  by the system ``Sphinx`` from the folder `docs` by the command ``make html``
  or ``make latexpdf``.

- The generated documentation of the package is published on the dedicated
  `Github page <https://mrkalepythonlib.github.io/gbj_pythonlib_sw/>`_.


Modules
=======

config
  Processing configuration files.

mqtt
  Communication with MQTT brokers and relevant cloud services,
  e.g., ThingSpeak.

statfilter
  Statistical smoothing and filtering measured data.

timer
  Managing timers utilizing threading.

trigger
  Managing numeric triggers. Triggers are identified usually by textual names.
  Each of them can be defined as upper trigger or lower trigger with particular
  threshold (trigger) value.

  Upper trigger
    It calls callback function(s) always when provided comparison value reaches
    or exceeds the threshold value, i.e., at every calling.

  Upper one-time trigger
    It calls callback function(s) only when provided comparison value reaches
    or exceeds the threshold value and at previous calling it was under the
    threshold.

  Lower trigger
    It calls callback function(s) always when the comparison value sinks to the
    threshold value or below, i.e., at every calling.

  Lower one-time trigger
    It calls callback function(s) only when the comparison value sinks to the
    threshold value or below and at previous calling it was above the
    threshold.

utils
  Auxilliary utilities and functions.
