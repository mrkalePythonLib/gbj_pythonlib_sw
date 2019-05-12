**********
Change log
**********
timer.py 0.3.0:
  Removed logger message at destroying object.
mqtt.py 0.4.0:
  - Added ``reconnect`` method
  - Moved client parameters from ``connect`` method to constructor
  - Added exception handling to some methods
mqtt.py 0.3.0:
  - Added configuration option *userdata* to MQTT ``connect`` method alongside
    other options.
