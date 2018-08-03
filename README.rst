**********************
Purpose of the package
**********************


The package ``gbj_pythonlib_sw`` contains a set of Python modules for supporting
ordinary python console applications and scripts. Those module are utilized as
libraries.

The documentation to each module of the package is located in the folder
`docs` and its subfolder `build` in form of HTML site. It contains detailed
documentation of modules' interfaces.


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
  Managing numeric triggers. Triggers are identified by textual names. Each of
  them can be defined as upper trigger o lower trigger with particular trigger
  value.

  Upper trigger
    It calls respective callback function when current value reaches or exceeds
    the trigger value.

  Lower trigger
    It calls callback function when the current value reaches or is less than
    trigger one.
