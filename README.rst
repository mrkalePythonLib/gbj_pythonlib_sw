****************
gbj_pythonlib_sw
****************
  
.. |modulePrefix| replace:: ``gbj_``

This package contains a set of Python modules for supporting ordinary python
console application and scripts.

Modules in the package are standalone and can be used individually and
separately in respective projects if reasonable.
  
Each module's name in the package is prefixed with |modulePrefix| in order
to prevent naming conflicts with other modules, if package modules are utilized individually.
  
Modules are imported without prefix |modulePrefix| to the package,
so that they can be referenced just with their root names, for instance::

    import gbj_config as config
  
Each module has its own description in the HTML file `<modulename>.html`.
  
  
Modules in package
==================

**gbj_config**
  Module for processing configuration files.

**gbj_mqtt**
  Module for MQTT brokers and relevant cloud services, e.g., ThingSpeak.

**gbj_statfilter**
  Module for statistical smoothing and filtering input data.

**gbj_timer**
  Module for managing timers utilizing threading.

**gbj_trigger**
  Module for managing numeric triggers.


