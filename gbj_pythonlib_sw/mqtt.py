#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for communicating with MQTT brokers."""
__version__ = "0.1.0"
__status__ = "Development"
__author__ = "Libor Gabaj"
__copyright__ = "Copyright 2018, " + __author__
__credits__ = []
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "libor.gabaj@gmail.com"


# Standard library modules
import time
import socket
import logging
# Third party modules
import paho.mqtt.client as mqttclient
import paho.mqtt.publish as mqttpublish


###############################################################################
# Module constants
###############################################################################
OPTION_CLIENTID = "clientid"
OPTION_HOST = "host"
OPTION_PORT = "port"
RESULTS = [
    "SUCCESS",
    "BAD PROTOCOL",
    "BAD CLIENT ID",
    "NO SERVER",
    "BAD CREDENTIALS",
    "NOT AUTHORISED",
]


###############################################################################
# Classes
###############################################################################
class MQTT(object):
    """Common MQTT management."""

    def __init__(self, config):
        """Initialize instance object - constructor.

        Positional arguments:
        ---------------------
        config -- object for access to a configuration file
        """
        self._logger = logging.getLogger(" ".join([__name__, __version__]))
        self._logger.debug("Instance of %s created", self.__class__.__name__)
        self._config = config
        self._connected = False

    def __str__(self):
        """Represent instance object as a string."""
        if self._config is None:
            return "Void configuration"
        else:
            return "Config file '{}'".format(self._config._file)

    def get_connected(self):
        """Return boolena connection flag."""
        return self._connected


class MqttBroker(MQTT):
    """Create MQTT client connecting to usually local MQTT broker.

    - The client utilizes MQTT topics and filter definitions from
      a configuration file.
    """

    # Predefined configuration file sections related to MQTT
    GROUP_BROKER = "MQTTbroker"
    GROUP_TOPICS = "MQTTtopics"
    GROUP_FILTERS = "MQTTfilters"

    def __str__(self):
        """Represent instance object as a string."""
        if hasattr(self, "_clientid"):
            return "MQTT client {}".format(self._clientid)
        else:
            return "No MQTT client active"

    def topic_def(self, option, section=GROUP_TOPICS):
        """Return topic definition as a 'topic,qos' tuple."""
        try:
            name, qos = self._config.option_split(option, section, ['0'])
            qos = int(qos)
        except TypeError:
            name = None
            qos = None
        return (name, qos)

    def topic_name(self, option, section=GROUP_TOPICS):
        """Return topic name from configuration MQTT topic definition."""
        name, _ = self.topic_def(option, section)
        return name

    def topic_qos(self, option, section=GROUP_TOPICS):
        """Return topic QoS from configuration MQTT topic definition."""
        _, qos = self.topic_def(option, section)
        return qos

    def _on_connect(self, client, userdata, flags, rc):
        """Process actions when the broker responds to a connection request.

        Positional arguments:
        ---------------------
        client -- the client instance for this callback
        userdata -- the private user data as set in Client() or user_data_set()
        flags -- response flags sent by the broker
        rc -- the connection result (result code)

        Desciption:
        -----------
        flags is a dict that contains response flags from the broker:
            flags['session present'] - this flag is useful for clients that are
            using clean session set to 0 only. If a client with clean
            session=0, that reconnects to a broker that it has previously
            connected to, this flag indicates whether the broker still has the
            session information for the client. If 1, the session still exists.

        The value of rc indicates success or not:
        0: Connection successful
        1: Connection refused - incorrect protocol version
        2: Connection refused - invalid client identifier
        3: Connection refused - server unavailable
        4: Connection refused - bad username or password
        5: Connection refused - not authorised
        6-255: Currently unused.
        """
        self._wating = False
        self._logger.debug("MQTT connect result %s: %s", rc, RESULTS[rc])
        if rc == 0:
            self._connected = True
        if self._cb_on_connect is not None:
            self._cb_on_connect(client, RESULTS[rc], flags, rc)

    def _on_disconnect(self, client, userdata, rc):
        """Process actions when the client disconnects from the broker.

        Positional arguments:
        ---------------------
        client -- the client instance for this callback
        userdata -- the private user data as set in Client() or user_data_set()
        rc -- the disconnection result (result code)
        """
        self._logger.debug("MQTT disconnect result %s: %s", rc, RESULTS[rc])
        if self._cb_on_disconnect is not None:
            self._cb_on_disconnect(client, RESULTS[rc], rc)
        self._client.loop_stop()
        self._connected = False

    def callback_filters(self, **kwargs):
        """Register callback functions for particular MQTT topic groups.

        Keyworded arguments:
        ---------------------
        key -- the key of the argument dictionary is a configuration option
               defining a topic, to which a topic filter is related.
        value -- the value of the argument dictionary is a tuple with callback
                 and section defining MQTT topic filter, if it is not
                 GROUP_FILTERS, or just a callback, e.g.
        server_test=mqtt_on_message_test
        server_sensor_temp=(mqtt_on_temp, ConfigMqtt.GROUP_TOPICS)

        - The method should be used before subscribing to respective filtered
          topics. The best place is in the on_connect callback.
        - The method can be called multiple times. For configuration option
          used at a previous call the filter callback is just updated. If the
          callback is None, the filter for correscponding topic is removed.
        """
        for option, definition in kwargs.iteritems():
            if isinstance(definition, tuple):
                callback = definition[0]
                section = definition[1]
            else:
                callback = definition
                section = self.GROUP_FILTERS
            topic = self.topic_name(option, section)
            self._logger.debug(
                "MQTT filter callback %s for topic %s",
                callback.__name__, topic)
            if topic is not None:
                if callback is None:
                    self._client.message_callback_remove(topic)
                else:
                    self._client.message_callback_add(topic, callback)

    def connect(self, **kwargs):
        """Connect to MQTT broker and set callback functions and credentials.

        Keyworded arguments:
        --------------------
        All key for callback function are root words from MQTT client callbacks
        without prefix "on_".

        connect -- callback launched after connection to MQTT broker
        disconnect -- callback launched after disconnection from MQTT broker
        subscribe -- callback launched after subscription to MQTT topics
        message -- callback launched after receiving message from MQTT topics
        username -- loging name of the registered user at MQTT broker
        password -- password of the registered user at MQTT broker
        """
        self._clientid = self._config.option(
            OPTION_CLIENTID, self.GROUP_BROKER,
            socket.gethostname()
        )
        self._client = mqttclient.Client(self._clientid)
        # Credentials
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)
        # Callbacks definition
        self._cb_on_connect = kwargs.pop("connect", None)
        self._cb_on_disconnect = kwargs.pop("disconnect", None)
        self._cb_on_subscribe = kwargs.pop("subscribe", None)
        self._cb_on_message = kwargs.pop("message", None)
        # Callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        if self._cb_on_subscribe is not None:
            self._client.on_subscribe = self._cb_on_subscribe
        if self._cb_on_message is not None:
            self._client.on_message = self._cb_on_message
        # Broker parameters
        host = self._config.option(
            OPTION_HOST, self.GROUP_BROKER, "localhost")
        port = int(self._config.option(
            OPTION_PORT, self.GROUP_BROKER, 1883))
        # Connect to broker
        self._logger.debug(
            "MQTT connection to broker %s:%s as client %s and user %s",
            host, port, self._clientid, username)
        self._wating = True
        try:
            self._client.loop_start()
            if username is not None:
                self._client.username_pw_set(username, password)
            self._client.connect(host, port)
        except Exception as errmsg:
            self._client.loop_stop()
            self._logger.error(
                "MQTT connection to %s:%s failed: %s",
                host, port, errmsg,
                exc_info=True)
            return
        # Waiting for connection
        while self._wating:
            time.sleep(0.2)

    def disconnect(self):
        """Disconnect from MQTT broker."""
        if hasattr(self, "_client"):
            self._client.loop_stop()
            self._client.disconnect()

    def subscribe_filters(self):
        """Subscribe to all MQTT topic filters.

        Returns:
        --------
        General exception with error code

        """
        if not self.get_connected():
            return
        for option in self._config.options(self.GROUP_FILTERS):
            topic, qos = self.topic_def(option, self.GROUP_FILTERS)
            result = self._client.subscribe(topic, qos)
            if result[0] == mqttclient.MQTT_ERR_SUCCESS:
                self._logger.debug(
                    "MQTT subscribe to filter %s, %s",
                    topic, qos)
            # elif result[0] == mqttclient.MQTT_ERR_NO_CONN:
            else:
                self._logger.error(
                    "MQTT filter subscribe result %s",
                    result[0])
                raise Exception(str(result[0]))

    def subscribe_topic(self, option, section=GROUP_TOPICS):
        """Subscribe to a MQTT topic determined by configuration option.

        Positional arguments:
        ---------------------
        option -- configuration file option to be read
        section -- configuration file section to be read from

        Returns:
        --------
        General exception with error code

        """
        if not self.get_connected():
            return
        topic, qos = self.topic_def(option, self.GROUP_TOPICS)
        result = self._client.subscribe(topic, qos)
        if result[0] == mqttclient.MQTT_ERR_SUCCESS:
            self._logger.debug(
                "MQTT subscribe to topic %s, %d",
                topic, qos)
        # elif result[0] == mqttclient.MQTT_ERR_NO_CONN:
        else:
            self._logger.error(
                "MQTT topic subscribe result %d",
                result[0])
            raise Exception(str(result[0]))

    def publish(self, message, option, section=GROUP_TOPICS):
        """Publish to a MQTT topic determined by configuration option.

        Positional arguments:
        ---------------------
        message -- data to be published
        option -- configuration file option to be read
        section -- configuration file section to be read from

        Returns:
        --------
        General exception with error message

        """
        if not self.get_connected():
            return
        topic, qos = self.topic_def(option, section)
        if topic is not None:
            self._client.publish(topic, message, qos)
            self._logger.debug(
                "MQTT publishing to topic %s, %d: %s",
                topic, qos, message)
        else:
            self._logger.error(
                "Publishing to MQTT topic option %s:[%s] failed",
                option, section)
            raise Exception("Unknown option or section")


class ThingSpeak(MQTT):
    """Connect and publish to ThingSpeak MQTT broker.

    - The client utilizes MQTT topics and filter definitions from
      a configuration file.
    - The class only provides single publishing to ThingSpeak, so that
      connecting and disconnecting to the ThingSpeak broker is automatic.
    """

    # Predefined configuration file sections and options related to ThingSpeak
    GROUP_BROKER = "ThingSpeak"
    OPTION_MQTT_API_KEY = "mqtt_api_key"
    OPTION_CHANNEL_ID = "channel_id"
    OPTION_WRITE_API_KEY = "write_api_key"
    OPTION_PUBLISH_DELAY = "publish_delay"

    def __init__(self, config):
        """Initialize instance object - constructor.

        Positional arguments:
        ---------------------
        config -- object for access to a configuration file
        """
        super(type(self), self).__init__(config)
        self._timestamp_publish_last = 0.0
        self._msgbuffer = []
        # Defaulted configuration parameters
        self._publish_delay = float(self._config.option(
            self.OPTION_PUBLISH_DELAY, self.GROUP_BROKER, 15.0))
        self._clientid = self._config.option(
            OPTION_CLIENTID, self.GROUP_BROKER, socket.gethostname())
        self._port = int(self._config.option(
            OPTION_PORT, self.GROUP_BROKER, 1883))
        # Configuration parameters without default value
        errtxt = "Undefined ThingSpeak config option {}"
        #
        self._host = self._config.option(OPTION_HOST, self.GROUP_BROKER)
        if self._host is None:
            errmsg = errtxt.format(OPTION_HOST)
            self._logger.error(errmsg)
            raise TypeError(errmsg)
        else:
            self._logger.debug(
                "ThingSpeak connection to broker %s:%s as client %s",
                self._host, self._port, self._clientid)
        #
        self._mqtt_api_key = self._config.option(
            self.OPTION_MQTT_API_KEY, self.GROUP_BROKER)
        if self._mqtt_api_key is None:
            errmsg = errtxt.format(self.OPTION_MQTT_API_KEY)
            self._logger.error(errmsg)
            raise TypeError(errmsg)
        #
        self._channel_id = self._config.option(
            self.OPTION_CHANNEL_ID, self.GROUP_BROKER)
        if self._channel_id is None:
            errmsg = errtxt.format(self.OPTION_CHANNEL_ID)
            self._logger.error(errmsg)
            raise TypeError(errmsg)
        #
        self._write_api_key = self._config.option(
            self.OPTION_WRITE_API_KEY, self.GROUP_BROKER)
        if self._write_api_key is None:
            errmsg = errtxt.format(self.OPTION_WRITE_API_KEY)
            self._logger.error(errmsg)
            raise TypeError(errmsg)

    def __str__(self):
        """Represent instance object as a string."""
        if hasattr(self, "_clientid"):
            return "ThingSpeak client {}".format(self._clientid)
        else:
            return "No ThingSpeak client active"

    def publish(self, fields={}, status=None):
        """Publish single message to the ThingSpeak MQTT broker.

        Positional arguments:
        ---------------------
        fields -- dictionary with ThingSpeak channel field numbers and values
                  for publishing, e.g., {1: 23.4, 2: 1}
        status -- text to be published in the ThingSpeak channel as a status

        - If a field number is outside the range 1 ~ 8, this field is ignored.
        - If a value is undefined or empty, the corresponding field or status
          is ignored.

        Returns:
        --------
        Boolean flag about real publishing to ThingSpeak
        General exception with error message from ThingSpeak

        """
        no_status = status is None or len(status) == 0
        # Construct message payload
        msgParts = []
        for field_num, field_value in fields.iteritems():
            if int(field_num) < 1 or int(field_num) > 8:
                continue
            if field_value is None:
                continue
            msgParts.append("field{}={}".format(field_num, field_value))
        if status is not None and len(status) > 0:
            msgParts.append("status={}".format(status))
        msgPayload = "&".join(msgParts)
        # Process frequent message
        if (time.time() - self._timestamp_publish_last) \
           < self._publish_delay:
            # Ignore message without status
            if no_status:
                self._logger.debug(
                    "Ignored frequent publishing to ThingSpeak")
            # Store message with status to buffer
            else:
                self._logger.debug(
                    "Buffered status message %s", msgPayload)
                self._msgbuffer.append(msgPayload)
            return False
        # Replace current message with status by stored message if any
        elif no_status:
            if len(self._msgbuffer) > 0:
                msgPayload = self._msgbuffer.pop(0)
                self._logger.debug(
                    "Retrieved buffered message %s", msgPayload)
        # Publish current message with status and throw away all stored ones
        else:
            self._msgbuffer = list()
        # Construct topic
        topicParts = ["channels", self._channel_id, "publish",
                      self._write_api_key]
        topic = "/".join(topicParts)
        # Publish payload
        if len(msgPayload) == 0:
            self._logger.debug("Nothing to publish to ThingSpeak")
            return False
        try:
            self._logger.debug("Publishing to ThingSpeak topic")
            mqttpublish.single(
                topic,
                payload=msgPayload,
                hostname=self._host,
                port=self._port,
                auth={"username": self._clientid,
                      'password': self._mqtt_api_key}
            )
            self._timestamp_publish_last = time.time()
            self._logger.debug("Published ThingSpeak message %s", msgPayload)
        except Exception as errmsg:
            self._logger.error(
                "Publishing to ThingSpeak failed with error %s:",
                errmsg, exc_info=True)
            return False
        return True

    def get_publish_delay(self):
        """Return current publish delay limit in seconds."""
        return self._publish_delay
