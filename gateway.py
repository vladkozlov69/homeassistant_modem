"""The sms gateway to interact with a GSM modem."""

import logging
import threading
import time
from collections.abc import Mapping

import gi
from homeassistant.components import logbook
from homeassistant.core import callback

from .const import (
    ATTR_CONNECTION_NAME,
    CONF_CONNECTION_NAME,
    DOMAIN,
    EVT_LTE_CONNECTED,
    EVT_LTE_DISCONNECTED,
    EVT_MODEM_CONNECTED,
    EVT_MODEM_DISCONNECTED,
    EVT_SMS_RECEIVED,
    SMS_SENSOR_ID,
    SMS_SENSOR_NAME,
)
from .exceptions import GSMGatewayException
from .sms_message import SmsMessage

gi.require_version("ModemManager", "1.0")
gi.require_version("NM", "1.0")

from gi.repository import Gio, GLib, ModemManager, NM

_LOG = logging.getLogger(__name__)

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

    def _get_config_value(self, key, default=None):
        """Read config values from YAML mappings or config-entry-like objects."""
        config = self._config_entry
        if config is None:
            return default
        if hasattr(config, "data") and isinstance(getattr(config, "data"), Mapping):
            data = config.data
            if key in data:
                return data[key]
            options = getattr(config, "options", None)
            if isinstance(options, Mapping) and key in options:
                return options[key]
        if isinstance(config, Mapping):
            return config.get(key, default)
        return getattr(config, key, default)

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

    def get_call_state(self, call):
        return ModemManager.CallState.get_string(call.get_state())

    def on_call_started(self, source_object, res, *user_data):
        """Callback method called when GSM call initiated"""
        voice = user_data[0][1]
        threading.Thread(target=self.call_close_function,
                         args=(source_object,voice,)).start()

    def call_close_function(self, call, voice):
        call_path = call.get_path()
        for x in range(1, 10):  # TODO: make this configurable
            _LOG.info('call in progress:' + call_path + ' - ' + self.get_call_state(call))
            if ModemManager.CallState.RINGING_OUT == call.get_state():
                break
            time.sleep(1)
        voice.hangup_all_sync(None)
        _LOG.info('Call hangup - ' + call_path)
        if voice.delete_call_sync(call_path, None):
            _LOG.info('Call deleted - ' + call_path)
        else:
            _LOG.info('Call not deleted - ' + call_path)
        _LOG.info('Calls before cleanup >>')
        for callvar in voice.list_calls_sync():
            if ModemManager.CallState.TERMINATED == callvar.get_state():
                _LOG.info('cleanup:' + callvar.get_path() + ' - ' + self.get_call_state(callvar))
                if voice.delete_call_sync(callvar.get_path(), None):
                    _LOG.info('Call deleted - ' + callvar.get_path())
                else:
                    _LOG.info('Call not deleted - ' + callvar.get_path())
        _LOG.info('Calls after cleanup >>')
        for callvar in voice.list_calls_sync():
            _LOG.info('calls:' + callvar.get_path() + ' - ' + self.get_call_state(callvar))
        _LOG.info('Calls after cleanup <<')

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
                _LOG.info('Modem added to bus: %s (%s) [%s]: %s' %
                      (modem.get_manufacturer(),
                       modem.get_model(),
                       modem.get_equipment_identifier(),
                       obj.get_object_path()))
                self._modem_object = obj
                self._messaging = obj.get_modem_messaging()
                self._messaging_notify_id = self._messaging.connect(
                    'notify::messages',
                    self.on_messaging_notify)
                self._hass.bus.fire(EVT_MODEM_CONNECTED, {})

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
        """ModemManager is now unavailable."""
        if self._available or self._initializing:
            _LOG.warning("ModemManager service not available in bus")
            self._modem_object = None

        if self._manager is not None and self._object_added_id:
            self._manager.disconnect(self._object_added_id)
            self._object_added_id = 0
        if self._manager is not None and self._object_removed_id:
            self._manager.disconnect(self._object_removed_id)
            self._object_removed_id = 0

        if self._messaging is not None and self._messaging_notify_id:
            try:
                self._messaging.disconnect(self._messaging_notify_id)
            except Exception:  # pragma: no cover - defensive cleanup
                _LOG.debug("Failed to disconnect messaging notify handler", exc_info=True)
        self._messaging_notify_id = 0
        self._messaging = None

        self._available = False

    def on_object_removed(self, manager, obj):
        """Modem disconnected."""
        _LOG.warning("modem unmanaged by ModemManager: %s", obj.get_object_path())

        if self._messaging is not None and self._messaging_notify_id:
            try:
                self._messaging.disconnect(self._messaging_notify_id)
            except Exception:  # pragma: no cover - defensive cleanup
                _LOG.debug("Failed to disconnect messaging notify handler", exc_info=True)
        self._messaging_notify_id = 0
        self._modem_object = None
        self._messaging = None
        self._hass.bus.fire(EVT_MODEM_DISCONNECTED, {})

    def on_messaging_notify(self, manager, obj):
        """Messaging callback"""
        if obj.name == 'messages':
            self._hass.bus.fire(EVT_SMS_RECEIVED, {})
        else:
            _LOG.warning('Unknown messaging notification: [%s]' % obj)

    def get_mm_modem(self, show_warning=True):
        """Gets ModemManager modem"""
        if self._modem_object is not None:
            return self._modem_object.get_modem()
        if show_warning:
            _LOG.warning(NO_MODEM_FOUND)
        return None

    def get_mm_modem3gpp(self, show_warning=True):
        """Gets ModemManager modem"""
        if self._modem_object is not None:
            return self._modem_object.get_modem3gpp()
        if show_warning:
            _LOG.warning(NO_MODEM_FOUND)
        return None

    def send_sms(self, number, message):
        """Send sms message via the worker."""
        sms_properties = ModemManager.SmsProperties.new()
        sms_properties.set_number(number)
        sms_properties.set_text(message)

        connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        manager = ModemManager.Manager.new_sync(
            connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None
        )
        if manager.get_name_owner() is None:
            _LOG.error("ModemManager not found in bus")
            raise GSMGatewayException("ModemManager not found in bus")

        sent = False
        for obj in manager.get_objects():
            messaging = obj.get_modem_messaging()
            if messaging is None:
                continue
            sms = messaging.create_sync(sms_properties)
            sms.send_sync()
            _LOG.debug("SMS sent via %s", messaging.get_object_path())
            sent = True

        if not sent:
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
                       user_data=(None, voice))
        except Exception as e:
            _LOG.error(e)

    def get_modem_state(self):
        """Get the current state of the modem."""
        modem = self.get_mm_modem(False)
        modem3gpp = self.get_mm_modem3gpp(False)
        if modem is None:
            return None
        modem_state = modem.get_state()
        operator = None
        if modem3gpp is not None:
            try:
                operator = modem3gpp.get_operator_name()
            except Exception:  # pragma: no cover - backend dependent
                operator = None
        return {
            "status": ModemManager.ModemState.get_string(modem_state),
            "signal": modem.get_signal_quality(),
            "operator": operator,
        }

    def _active_connection_added_cb(self, client, connection):
        _LOG.debug("NM connection added: %s", connection.get_uuid())

    def _active_connection_removed_cb(self, client, connection):
        _LOG.debug("NM connection removed: %s", connection.get_uuid())

    def _activate_connection_async_cb(self, source_object, res):
        _LOG.debug("activate_connection_async_cb %s %s" % (source_object, res))
        self._hass.bus.async_fire(EVT_LTE_CONNECTED, {})

    def _deactivate_connection_async_cb(self, source_object, res):
        _LOG.debug("deactivate_connection_async_cb %s %s" % (source_object, res))
        self._hass.bus.async_fire(EVT_LTE_DISCONNECTED, {})

    def lte_up(self):
        """LTE Up."""
        conn_name = self._get_config_value(CONF_CONNECTION_NAME) or self._get_config_value(
            ATTR_CONNECTION_NAME
        )
        _LOG.debug("Configured connection name: %s", conn_name)
        if not conn_name:
            _LOG.warning("No LTE connection name configured")
            return

        try:
            client = NM.Client.new(None)
            client.connect("active-connection-added", self._active_connection_added_cb)
            connections = client.get_connections() or []
            for conn in connections:
                _LOG.debug("=== %s : %s ===", conn.get_id(), conn.get_path())
                if conn.get_id() == conn_name:
                    _LOG.info("Activating %s %s", conn.get_id(), conn.get_path())
                    client.activate_connection_async(
                        conn, None, None, None, self._activate_connection_async_cb
                    )
                    return
            _LOG.warning("Configured LTE connection not found: %s", conn_name)
        except Exception:
            _LOG.exception("Failed to activate LTE connection")

    def lte_down(self):
        """LTE Down."""
        conn_name = self._get_config_value(CONF_CONNECTION_NAME) or self._get_config_value(
            ATTR_CONNECTION_NAME
        )
        _LOG.debug("Configured connection name: %s", conn_name)
        if not conn_name:
            _LOG.warning("No LTE connection name configured")
            return

        try:
            client = NM.Client.new(None)
            client.connect("active-connection-removed", self._active_connection_removed_cb)
            connections = client.get_active_connections() or []
            for conn in connections:
                _LOG.debug("=== %s : %s ===", conn.get_id(), conn.get_path())
                if conn.get_id() == conn_name:
                    _LOG.info("Deactivating %s %s", conn.get_id(), conn.get_path())
                    client.deactivate_connection_async(
                        conn, None, self._deactivate_connection_async_cb
                    )
                    return
            _LOG.debug("Configured LTE connection is not active: %s", conn_name)
        except Exception:
            _LOG.exception("Failed to deactivate LTE connection")

    def get_lte_state(self):
        """Return True if the configured LTE connection is active."""
        conn_name = self._get_config_value(CONF_CONNECTION_NAME) or self._get_config_value(
            ATTR_CONNECTION_NAME
        )
        if not conn_name:
            return False

        try:
            client = NM.Client.new(None)
            connections = client.get_active_connections() or []
            for conn in connections:
                if conn.get_id() == conn_name:
                    return True
        except Exception:
            _LOG.exception("Failed to read LTE connection state")
            return False
        return False


    def get_sms_messages(self):
        """Return received SMS messages from the modem."""
        if self._messaging is None:
            return None
        try:
            sms_list = self._messaging.list_sync(None) or []
        except Exception:
            _LOG.exception("Failed to list SMS messages")
            return None

        messages = []
        for message in sms_list:
            try:
                if ModemManager.SmsState.RECEIVED == message.get_state():
                    messages.append(
                        SmsMessage(
                            path=message.get_path(),
                            number=message.get_number(),
                            text=message.get_text(),
                            timestamp=message.get_timestamp(),
                        )
                    )
            except Exception:
                _LOG.exception("Failed to read SMS message")
        return messages

    async def delete_sms_message(self, message_path):
        """Delete SMS message from modem storage."""
        messaging = self._messaging
        if messaging is None:
            _LOG.error(NO_MODEM_FOUND)
            raise GSMGatewayException(NO_MODEM_FOUND)

        try:
            delete_sync = getattr(messaging, "delete_sync", None)
            if delete_sync is not None:
                await self._hass.async_add_executor_job(delete_sync, message_path)
            else:
                call_delete = getattr(messaging, "call_delete", None)
                if call_delete is None:
                    raise GSMGatewayException("Messaging interface does not support delete")
                result = call_delete(message_path, None)
                if hasattr(result, "__await__"):
                    await result
        except GSMGatewayException:
            raise
        except Exception as err:
            _LOG.exception("Failed to delete SMS %s", message_path)
            raise GSMGatewayException(str(err)) from err

        _LOG.info("Deleted SMS %s", message_path)


def create_modem_gateway(config_entry, hass):
    """Create the modem gateway."""
    gateway = Gateway(config_entry, hass)
    return gateway
