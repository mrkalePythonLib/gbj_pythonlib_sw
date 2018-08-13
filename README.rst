**********************
Purpose of the package
**********************


The package ``gbj_pythonlib_sw`` contains a set of Python modules for supporting
ordinary python console applications and scripts. Those module are utilized as
libraries.

The documentation configuration for the package is located in the folder
`docs/source`. It can be generated from this folder by the by command
``make html``.


Modules
=======

config
  Processing configuration files.

mqtt
  Communication with MQTT brokers and relevant cloud services, e.g., ThingSpeak.

statfilter
  Statistical smoothing and filtering measured data.

timer
  Managing timers utilizing threading.

trigger
  Managing numeric triggers. Triggers are identified usualy by textual names.
  Each of them can be defined as upper trigger or lower trigger with particular
  threshold (trigger) value.

  Upper trigger
    It calls callback function(s) when provided comparison value reaches or
    exceeds the threshold value.

  Lower trigger
    It calls callback function(s) when the comparison value sinks to the
    threshold value or below.
