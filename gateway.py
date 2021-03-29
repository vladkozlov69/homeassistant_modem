"""The sms gateway to interact with a GSM modem."""
import logging

import gi
import NetworkManager
import time

from .const import ATTR_CONNECTION_NAME
from .sms_message import SmsMessage

gi.require_version('ModemManager', '1.0')
gi.require_version("NM", "1.0")

from gi.repository import GLib, Gio, ModemManager

# from homeassistant.core import callback

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)

NO_MODEM_FOUND = "No modem found"


class ModemGatewayException(Exception):
    """Modem Gateway exception."""


class Gateway:
    """SMS gateway to interact with a GSM modem."""
    _config_entry = None

    def on_call_started(self, source_object, res, *user_data):
        """Callback method called when GSM call initiated"""
        for x in range(1, 20):  # TODO: make this configurable
            print(source_object.get_state(), user_data[0][1].get_state())
            time.sleep(1)
        user_data[0][0].quit()

    def __init__(self, config_entry, hass):
        """Initialize the sms gateway."""
        self._hass = hass
        self._config_entry = config_entry

    @staticmethod
    def get_mm_object(show_warning=True):
        """Gets ModemManager object"""
        connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        manager = ModemManager.Manager.new_sync(
            connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START,
            None)
        if manager.get_name_owner() is None:
            _LOG.error("ModemManager not found in bus")
            return None
        if (len(manager.get_objects()) == 0):
            if (show_warning):
                _LOG.warning("Modem is not connected")
            return None
        return manager.get_objects()[0]

    def get_mm_modem(self, show_warning=True):
        """Gets ModemManager modem"""
        mm_object = self.get_mm_object(show_warning)
        if mm_object is not None:
            return mm_object.get_modem()
        if show_warning:
            _LOG.warning(NO_MODEM_FOUND)
        return None

    def send_sms(self, number, message):
        """Send sms message via the worker."""
        sms_properties = ModemManager.SmsProperties.new()
        sms_properties.set_number(number)
        sms_properties.set_text(message)

        mm_object = self.get_mm_object()
        if mm_object is None:
            _LOG.error(NO_MODEM_FOUND)
            raise ModemGatewayException(NO_MODEM_FOUND)

        messaging = mm_object.get_modem_messaging()

        sms = messaging.create_sync(sms_properties)
        sms.send_sync()
        _LOG.info('%s: sms sent', messaging.get_object_path())

    def dial_voice(self, number):
        """Initiale voice call"""
        call_properties = ModemManager.CallProperties.new()
        call_properties.set_number(number)
        main_loop = GLib.MainLoop()

        mm_object = self.get_mm_object()
        if mm_object is None:
            _LOG.error(NO_MODEM_FOUND)
            raise ModemGatewayException(NO_MODEM_FOUND)

        voice = mm_object.get_modem_voice()

        try:
            call = voice.create_call_sync(call_properties, None)
            call.start(cancellable=None, callback=self.on_call_started,
                       user_data=(main_loop, call_properties))
            main_loop.run()
        except Exception as e:
            main_loop.quit()
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

        conn_name = self._config_entry.options[ATTR_CONNECTION_NAME]
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("connection name: %s", conn_name)

        # Find the connection
        connections = NetworkManager.Settings.ListConnections()
        connections = {x.GetSettings()['connection']['id']: x
                       for x in connections}

        conn = connections.get(conn_name)

        if conn is None:
            _LOG.warning("No connection name %s found", conn_name)
            raise ModemGatewayException("No connection %s found" % conn_name)

        # Find a suitable device
        ctype = conn.GetSettings()['connection']['type']
        if ctype == 'vpn':
            for dev in NetworkManager.NetworkManager.GetDevices():
                if (dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED
                   and dev.Managed):
                    break
            else:
                _LOG.error("No active, managed device %s found", ctype)
                raise ModemGatewayException("No active managed device %s found"
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
                              self._config_entry.options[ATTR_CONNECTION_NAME],
                              NetworkManager.NetworkManager.GetAllDevices()))

        # print the list
        if _LOG.isEnabledFor(logging.INFO):
            for index, device in enumerate(devices):
                print(index, ")", device.Interface,
                      " Active:", device.ActiveConnection.Id)

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
        mm_object = self.get_mm_object()
        if mm_object is None:
            _LOG.error(NO_MODEM_FOUND)
            raise ModemGatewayException(NO_MODEM_FOUND)

        messaging = mm_object.get_modem_messaging()
        sms_list = messaging.list_sync(None)
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


def create_modem_gateway(config_entry, hass):
    """Create the modem gateway."""
    gateway = Gateway(config_entry, hass)
    return gateway
