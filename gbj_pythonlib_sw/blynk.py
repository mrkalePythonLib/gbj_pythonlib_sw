# -*- coding: utf-8 -*-
"""Module for communicating with Blynk cloud."""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = ['Volodymyr Shymanskyy']
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


# Standard library modules
import logging
import time
import struct
import socket
# Third party modules


###############################################################################
# Module constants
###############################################################################
# Configuration options
GROUP_BROKER = 'Blynk'
"""str: Configuration section with Blynk parameters."""

OPTION_API_KEY = 'blynk_auth'
"""str: Configuration option with Blynk API key."""

# Blynk colors
COLOR_GREEN = "#23C48E"
"""str: Color code recognized by Blynk for green."""

COLOR_BLUE = "#04C0F8"
"""str: Color code recognized by Blynk for blue."""

COLOR_YELLOW = "#ED9D00"
"""str: Color code recognized by Blynk for yellow."""

COLOR_RED = "#D3435C"
"""str: Color code recognized by Blynk for red."""

COLORDARK_BLUE = "#5F7CD8"
"""str: Color code recognized by Blynk for dark blue."""


###############################################################################
# Enumeration and parameter classes
###############################################################################
class Msg:
    """Message types."""

    (
        RSP, LOGIN, PING, TWEET, EMAIL, NOTIFY, BRIDGE, HW_SYNC, INTERNAL, 
        PROPERTY, HW, HW_LOGIN, EVENT_LOG, 
    ) = (0, 2, 6, 12, 13, 14, 15, 16, 17, 19, 20, 29, 64,)


class Status:
    """Status types."""

    (
        SUCCESS, INVALID_TOKEN, DISCONNECTED, CONNECTING, CONNECTED,
    ) = (200, 9, 0, 1, 2)


###############################################################################
# Classes
###############################################################################
class BlynkProtocol:
    """Implementation of Blynk protocol.


    Keyword Arguments
    -----------------
    server : str
        Blynk server address either in the cloude or local one.
        Default is cloude Blynk server.
    port : int
        TCP port at which the Blynk server listens.
        Default is 80 for plain HTTP without security.
    auth : str
        Authorization token taken from a Blynk mobile project.
    heartbeat : int
        Heartbeat interval in seconds for checking connection.
    buffin : int
        Input buffer length in bytes for receiving messaged from the cloud.

    """
    
    VERSION = '0.2.0'
    """str: Version of the Blynk."""
    
    CONN_TIMEOUT = 0.05
    """float: Connection timeout in seconds."""

    def __init__(self, auth, **kwargs):
        self.auth = auth
        self.server = kwargs.pop('server', 'blynk-cloud.com')
        self.port = kwargs.pop('port', 80)
        self.heartbeat = kwargs.pop('heartbeat', 10) * 1000
        self.buffin = kwargs.pop('buffin', 1024)
        # Internal parameters
        self.callbacks = {}
        self.state = Status.DISCONNECTED
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug(
            'Instance of %s created',
            self.__class__.__name__,
        )
        # self.connect()

    def __str__(self):
        """Represent instance object as a string."""
        return 'BlynkProtocol'

    def __repr__(self):
        """Represent instance object officially."""
        return 'BlynkProtocol({}, {}, {})'.format(
                repr(self.auth),
                repr(self.heartbeat),
                repr(self.buffin)
            )

    def _gettime(self):
        """Provide current time in milliseconds."""
        return int(time.time() * 1000)

    def _write(self, data):
        """Send provided data to the cloud."""
        self.conn.send(data)

    def _send(self, cmd, *args, **kwargs):
        if 'id' in kwargs:
            id = kwargs['id']
        else:
            id = self.msg_id
            self.msg_id += 1
            if self.msg_id > 0xFFFF:
                self.msg_id = 1
        if cmd == Msg.RSP:
            data = b''
            dlen = args[0]
        else:
            data = ('\0'.join(map(str, args))).encode('utf8')
            dlen = len(data)
        self._logger.debug('Command=%s, id=%s, args: %s', cmd, id, args)
        msg = struct.pack("!BHH", cmd, id, dlen) + data
        self.lastSend = self._gettime()
        self._write(msg)

    def connect(self):
        """Connect to the cloud or local server."""
        try:
            self.conn = socket.socket()
            self.conn.connect(socket.getaddrinfo(self.server, self.port)[0][4])
            try:
                self.conn.settimeout(CONN_TIMEOUT)
            except:
                self.conn.settimeout(0)
            if self.state != Status.DISCONNECTED:
                return
            self.msg_id = 1
            self.lastRecv = self._gettime()
            self.lastSend, self.lastPing = 0, 0
            self.bin = b''
            self.state = Status.CONNECTING
            self._send(Msg.HW_LOGIN, self.auth)
        except:
            self._logger.error(
                'Connection with the Blynk server %s:%d failed',
                self.server,
                self.port
                )
            errmsg = f'Connection with the Blynk server' \
                     '{self.server}:{self.port} failed'
            raise ValueError(errmsg)

    def run(self):
        data = b''
        try:
            data = self.conn.recv(self.buffin)
        except KeyboardInterrupt:
            raise
        except:
            # TODO: handle disconnect
            pass
        self.process(data)

    def ON(self, event):
        parent = self

        class Decorator:
            def __init__(self, func):
                self.func = func
                parent.callbacks[event] = func

            def __call__(self):
                return self.func()
        return Decorator

    def VIRTUAL_READ(self, pin):
        parent = self

        class Decorator():
            def __init__(self, func):
                self.func = func
                parent.callbacks[f'readV{pin}'] = func

            def __call__(self):
                return self.func()
        return Decorator

    def VIRTUAL_WRITE(self, pin):
        parent = self

        class Decorator():
            def __init__(self, func):
                self.func = func
                parent.callbacks[f'V{pin}'] = func

            def __call__(self):
                return self.func()
        return Decorator

    def on(self, event, func):
        self.callbacks[event] = func

    def emit(self, event, *args, **kwargs):
        self._logger.debug('Event %s with args: %s', event, args)
        if event in self.callbacks:
            self.callbacks[event](*args, **kwargs)

    def virtual_write(self, pin, *val):
        """Send virtual pin value to the server."""
        self._send(Msg.HW, 'vw', pin, *val)

    def set_property(self, pin, prop, *val):
        """Send property of a pin to the server."""
        self._send(Msg.PROPERTY, pin, prop, *val)

    def sync_virtual(self, *pins):
        self._send(Msg.HW_SYNC, 'vr', *pins)

    def notify(self, msg):
        self._send(Msg.NOTIFY, msg)

    def tweet(self, msg):
        self._send(Msg.TWEET, msg)

    def log_event(self, event, descr=None):
        if descr == None:
            self._send(Msg.EVENT_LOG, event)
        else:
            self._send(Msg.EVENT_LOG, event, descr)

    def disconnect(self):
        if self.state == Status.DISCONNECTED:
            return
        self.state = Status.DISCONNECTED
        self.emit('disconnected')

    def process(self, data=b''):
        if self.state not in [Status.CONNECTING, Status.CONNECTED]:
            return
        now = self._gettime()
        if now - self.lastRecv > self.heartbeat+(self.heartbeat//2):
            return self.disconnect()
        if (now - self.lastPing > self.heartbeat//10
            and (now - self.lastSend > self.heartbeat
              or now - self.lastRecv > self.heartbeat
              )
            ):
            self._send(Msg.PING)
            self.lastPing = now
        if data is not None and len(data):
            self.bin += data
        while True:
            if len(self.bin) < 5:
                return
            cmd, i, dlen = struct.unpack("!BHH", self.bin[:5])
            if i == 0:
                return self.disconnect()
            self.lastRecv = now
            if cmd == Msg.RSP:
                self.bin = self.bin[5:]
                self._logger.debug(
                    'Command=%s, iter=%d, length: %d',
                    cmd, i, dlen
                )
                if self.state == Status.CONNECTING and i == 1:
                    if dlen == Status.SUCCESS:
                        self.state = Status.CONNECTED
                        dt = now - self.lastSend
                        self._send(
                            Msg.INTERNAL,
                            'ver', self.VERSION,
                            'h-beat', self.heartbeat//1000,
                            'buff-in', self.buffin,
                            'dev',
                            'python'
                        )
                        try:
                            self.emit('connected', ping=dt)
                        except TypeError:
                            self.emit('connected')
                    else:
                        if dlen == Status.INVALID_TOKEN:
                            self._logger.critical('Invalid auth token')
                        return self.disconnect()
            else:
                if dlen >= self.buffin:
                    self._logger.error('Command too big: %d', dlen)
                    return self.disconnect()
                if len(self.bin) < 5 + dlen:
                    return
                data = self.bin[5:5+dlen]
                self.bin = self.bin[5+dlen:]
                args = list(map(lambda x: x.decode('utf8'), data.split(b'\0')))
                self._logger.debug(
                    'Command=%s, iter=%d, args: %s',
                     cmd, i, args
                )
                if cmd == Msg.PING:
                    self._send(Msg.RSP, Status.SUCCESS, id=i)
                elif cmd in [Msg.HW, Msg.BRIDGE]:
                    if args[0] == 'vw':
                        self.emit("V" + args[1], args[2:])
                        self.emit("V*", args[1], args[2:])
                    elif args[0] == 'vr':
                        self.emit("readV"+args[1])
                        self.emit("readV*", args[1])
                elif cmd == Msg.INTERNAL:
                    self.emit("int_" + args[1], args[2:])
                else:
                    self._logger.error('Unexpected command: %s', cmd)
                    return self.disconnect()



class BlynkDevice(BlynkProtocol):
    """Acting as a hardware device controlled by Blynk.

    Arguments
    ---------
    config : object
        Object for access to a configuration INI file.
        It is instance of the class ``Config`` from this package's module
        ``config``.
        Particular configuration file is already open.
        Injection of the config file object to this class instance is a form
        of attaching that file to this object.


    Keyword Arguments
    -----------------
    server : str
        Blynk server address either in the cloude or local one.
        Default is cloude Blynk server.
    port : int
        TCP port at which the Blynk server listens.
        Default is 80 for plain HTTP without security.
    auth : str
        Authorization token taken from a Blynk mobile project.
    heartbeat : int
        Heartbeat interval in seconds for checking connection.
    buffin : int
        Input buffer length in bytes for receiving messaged from the cloud.


    Notes
    -----
    This class should not be instanciated. It serves as a abstract class and
    a parent class for operational classes for particular Blynk wrapper
    modules.

    See Also
    --------
    config.Config : Class for managing configuration INI files.

    """

    def __init__(self, config, **kwargs):
        """Create the class instance - constructor."""
        self._config = config
        self._connected = False
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug(
            'Instance of %s created',
            self.__class__.__name__,
            )
        if type(self._config) is object:
            api_key = self._config.option(OPTION_API_KEY, GROUP_BROKER)
            super().__init__(api_key, **kwargs)

    def __str__(self):
        """Represent instance object as a string."""
        if self._config is None:
            return 'Void configuration'
        else:
            return 'Config file "{}"'.format(self._config._file)

    def __repr__(self):
        """Represent instance object officially."""
        return 'BlynkDevice({})'.format(
            repr(self._config),
        )
