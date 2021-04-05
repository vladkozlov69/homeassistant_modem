"""The sms gateway to interact with a GSM modem."""
import logging

import gi
import NetworkManager
import time
import threading

from homeassistant.core import callback

from .const import (
    ATTR_CONNECTION_NAME,
    EVT_MODEM_CONNECTED,
    EVT_MODEM_DISCONNECTED,
    EVT_SMS_RECEIVED
)

from .sms_message import SmsMessage
from .exceptions import GSMGatewayException

gi.require_version('ModemManager', '1.0')
gi.require_version("NM", "1.0")

from gi.repository import GLib, Gio, ModemManager

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)

NO_MODEM_FOUND = "No modem found"


class Gateway:
    """SMS gateway to interact with a GSM modem."""
    _config_entry = None
    _manager = None
    _glib_loop_task = None
    _initializing = True
    _available = False
    _messaging = None
    _do_stop = False
    # IDs for added/removed signals
    _object_added_id = 0
    _object_removed_id = 0
    # ID for notify signal
    _messaging_notify_id = 0
    _modem_object = None

    def __init__(self, config_entry, hass):
        """Initialize the sms gateway."""
        self._hass = hass
        self._config_entry = config_entry

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        await self.async_start_glib()

    @callback
    def stop_glib_loop(self, event):
        """Close resources."""
        self._do_stop = True

    def glib_loop_function(self, loop):
        _LOG.debug("GLib loop : starting")
        while self._do_stop is False:
            context = loop.get_context()
            if context.pending():
                context.iteration(False)
            time.sleep(0.01)
        _LOG.info("GLib loop : closed")

    async def async_start_glib(self):
        """GLib loop."""
        self._initializing = True
        connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._manager = ModemManager.Manager.new_sync(
            connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START,
            None)

        self._available = False
        self._manager.connect('notify::name-owner', self.on_name_owner)
        self.on_name_owner(self._manager, None)
        self._initializing = False
        main_loop = GLib.MainLoop()
        threading.Thread(target=self.glib_loop_function,
                         args=(main_loop,)).start()

    def on_call_started(self, source_object, res, *user_data):
        """Callback method called when GSM call initiated"""
        for x in range(1, 20):  # TODO: make this configurable
            print(source_object.get_state(), user_data[0][1].get_state())
            time.sleep(1)

    def on_name_owner(self, manager, prop):
        """Name owner updates"""
        if self._manager.get_name_owner():
            self.set_available()
        else:
            self.set_unavailable()

    def on_object_added(self, manager, obj):
        """Object added"""
        if self._modem_object is None:
            modem = obj.get_modem()
            if modem.get_state() == ModemManager.ModemState.FAILED:
                _LOG.error('%s ignoring failed modem' % obj.get_object_path())
                pass
            else:
                _LOG.info('Modem added to bus %s' % modem)
                self._modem_object = obj
                self._messaging = obj.get_modem_messaging()
                self._messaging_notify_id = self._messaging.connect(
                    'notify::messages',
                    self.on_messaging_notify)
                self._hass.bus.async_fire(EVT_MODEM_CONNECTED, {})

    def set_available(self):
        """ModemManager is now available"""
        if self._available is False or self._initializing:
            _LOG.info('ModemManager service is available in bus')
        self._object_added_id = self._manager.connect('object-added',
                                                      self.on_object_added)
        self._object_removed_id = self._manager.connect('object-removed',
                                                        self.on_object_removed)
        self._available = True

        # Initial scan
        if (self._initializing):
            for obj in self._manager.get_objects():
                self.on_object_added(self._manager, obj)

    def set_unavailable(self):
        """ModemManager is now unavailable"""
        if self._available or self._initializing:
            _LOG.warn('ModemManager service not available in bus')
            self._modem_object = None

        if self._object_added_id:
            self._manager.disconnect(self._object_added_id)
            self._object_added_id = 0
        if self._object_removed_id:
            self._manager.disconnect(self._object_removed_id)
            self._object_removed_id = 0

        if self._messaging_notify_id:
            self._messaging.disconnect(self._messaging_notify_id)
            self._messaging_notify_id = 0

        self._available = False

    def on_object_removed(self, manager, obj):
        """Modem disconnected"""
        _LOG.warn('modem unmanaged by ModemManager: %s'
                  % obj.get_object_path())

        self._messaging.disconnect(self._messaging_notify_id)
        self._messaging_notify_id = 0

        self._modem_object = None
        self._messaging = None
        self._hass.bus.async_fire(EVT_MODEM_DISCONNECTED, {})

    def on_messaging_notify(self, manager, obj):
        """Messaging callback"""
        _LOG.info(obj)
        _LOG.info(obj.value_type)
        _LOG.info(obj.flags)
        _LOG.info(obj.blurb)
        _LOG.info(dir(obj))
        if (obj.name == 'messages'):
            self._hass.bus.async_fire(EVT_SMS_RECEIVED, {})
        else:
            _LOG.warn('Unknown messaging notification: [%s]' % obj)

    def get_mm_modem(self, show_warning=True):
        """Gets ModemManager modem"""
        if self._modem_object is not None:
            return self._modem_object.get_modem()
        if show_warning:
            _LOG.warning(NO_MODEM_FOUND)
        return None

    def send_sms(self, number, message):
        """Send sms message via the worker."""
        sms_properties = ModemManager.SmsProperties.new()
        sms_properties.set_number(number)
        sms_properties.set_text(message)

        messaging = self._messaging
        if messaging is not None:
            sms = messaging.create_sync(sms_properties)
            sms.send_sync()
            _LOG.info('%s: sms sent', messaging.get_object_path())
        else:
            _LOG.error(NO_MODEM_FOUND)
            raise GSMGatewayException(NO_MODEM_FOUND)

    def dial_voice(self, number):
        """Initiale voice call"""
        call_properties = ModemManager.CallProperties.new()
        call_properties.set_number(number)

        mm_object = self._modem_object
        if mm_object is None:
            _LOG.error(NO_MODEM_FOUND)
            raise GSMGatewayException(NO_MODEM_FOUND)

        voice = mm_object.get_modem_voice()

        try:
            call = voice.create_call_sync(call_properties, None)
            call.start(cancellable=None, callback=self.on_call_started,
                       user_data=(None, call_properties))
        except Exception as e:
            _LOG.error(e)
        finally:
            print('cleanup current call:', call.get_path())
            print(call.get_state())
            voice.delete_call_sync(call.get_path(), None)
            for callvar in voice.list_calls_sync():
                print('calls:', callvar.get_path())
                if ModemManager.CallState.TERMINATED == callvar.get_state():
                    print(callvar.get_state())
                    voice.delete_call_sync(callvar.get_path(), None)

    def get_modem_state(self):
        """Get the current state of the modem."""
        modem = self.get_mm_modem(False)
        if modem is None:
            # _LOG.warning(NO_MODEM_FOUND)
            return None
        modem_state = modem.get_state()
        return {
            'status': ModemManager.ModemState.get_string(modem_state),
            'signal': modem.get_signal_quality(),
            'operator': modem.get_sim_sync().get_operator_name()
        }

    def lte_up(self):
        """LTE Up."""
        conn_name = self._config_entry.data[ATTR_CONNECTION_NAME]
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("connection name: %s", conn_name)

        # Find the connection
        _LOG.debug('At====== 1')
        connections = NetworkManager.Settings.ListConnections()
        _LOG.debug('At====== 2')
        connections = {x.GetSettings()['connection']['id']: x
                       for x in connections}
        _LOG.debug('At====== 3')
        conn = connections.get(conn_name)

        if conn is None:
            _LOG.warning("No connection name %s found", conn_name)
            raise GSMGatewayException("No connection %s found" % conn_name)

        # Find a suitable device
        ctype = conn.GetSettings()['connection']['type']
        if ctype == 'vpn':
            for dev in NetworkManager.NetworkManager.GetDevices():
                if (dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED
                   and dev.Managed):
                    break
            else:
                _LOG.error("No active, managed device %s found", ctype)
                raise GSMGatewayException("No active managed device %s found"
                                          % ctype)
        else:
            dtype = {
                '802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI,
                '802-3-ethernet': NetworkManager.NM_DEVICE_TYPE_ETHERNET,
                'gsm': NetworkManager.NM_DEVICE_TYPE_MODEM,
            }.get(ctype, ctype)
            devices = NetworkManager.NetworkManager.GetDevices()

            for dev in devices:
                if (dev.DeviceType == dtype and
                   dev.State == NetworkManager.NM_DEVICE_STATE_DISCONNECTED):
                    break
            else:
                _LOG.error('No suitable and available %s device found', ctype)
                return

        # And connect
        NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")

    def lte_down(self):
        """LTE Down."""
        # list of devices with active connection
        devices = list(filter(lambda _dev: _dev.ActiveConnection is not None
                              and _dev.ActiveConnection.Id ==
                              self._config_entry.data[ATTR_CONNECTION_NAME],
                              NetworkManager.NetworkManager.GetAllDevices()))

        # print the list
        for index, device in enumerate(devices):
            _LOG.info("%s) %s Active:%s",
                      index, device.Interface, device.ActiveConnection.Id)

        if devices:
            active_conn = devices[0].ActiveConnection
            print(active_conn.Id)
            NetworkManager.NetworkManager.DeactivateConnection(active_conn)

        else:
            _LOG.warning('No active LTE connection found')

    def get_lte_devices(self):
        """Returns list of LTE devices"""
        all_devices = NetworkManager.NetworkManager.GetAllDevices()
        return list(filter(lambda _dev: _dev.ActiveConnection is not None
                           and _dev.ActiveConnection.Id ==
                           self._config_entry.options[ATTR_CONNECTION_NAME],
                           all_devices))

    def get_sms_messages(self):
        if self._messaging is not None:
            sms_list = self._messaging.list_sync(None)
            messages = []
            for message in sms_list:
                if(ModemManager.SmsState.RECEIVED == message.get_state()):
                    messages.append(SmsMessage(
                                        path=message.get_path(),
                                        number=message.get_number(),
                                        text=message.get_text(),
                                        timestamp=message.get_timestamp()
                                    ))
            return messages
        else:
            return None

    def delete_sms_message(self, message_path):
        if self._messaging is None:
            _LOG.error(NO_MODEM_FOUND)
            raise GSMGatewayException(NO_MODEM_FOUND)
        else:
            self._messaging.call_delete_sync(message_path)
            _LOG.info('Deleted SMS ' + message_path)


def create_modem_gateway(config_entry, hass):
    """Create the modem gateway."""
    gateway = Gateway(config_entry, hass)
    return gateway
