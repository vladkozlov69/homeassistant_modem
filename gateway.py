"""The sms gateway to interact with a GSM modem."""
import logging

import sys, signal, gi, NetworkManager

gi.require_version('ModemManager', '1.0')
gi.require_version("NM", "1.0")

from gi.repository import GLib, GObject, Gio, ModemManager, NM

from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ModemGatewayException(Exception):
    """I2C-HATs exception."""

class Gateway:
    """SMS gateway to interact with a GSM modem."""

    def __init__(self, hass):
        """Initialize the sms gateway."""
        self._hass = hass

    def get_mm_object(self):
        """Gets ModemManager object"""
        connection = Gio.bus_get_sync (Gio.BusType.SYSTEM, None)
        manager = ModemManager.Manager.new_sync (connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None)
        if manager.get_name_owner() is None:
            _LOGGER.error("ModemManager not found in bus")
            return
        return manager.get_objects()[0]

    def get_mm_modem(self):
        """Gets ModemManager modem"""
        return self.get_mm_object().get_modem()

    def send_sms(self, number, message):
        """Send sms message via the worker."""
        sms_properties = ModemManager.SmsProperties.new ()
        sms_properties.set_number(number)
        sms_properties.set_text(message)

        messaging = self.get_mm_object().get_modem_messaging()

        sms = messaging.create_sync(sms_properties)
        sms.send_sync()
        _LOGGER.info('%s: sms sent' % messaging.get_object_path())


    def get_operator_name(self):
        """Get the IMEI of the device."""
        return self.get_mm_modem().get_sim_sync().get_operator_name()


    def get_signal_strength(self):
        """Get the current signal level of the modem."""
        return self.get_mm_modem().get_signal_quality()

    def get_modem_state(self):
        """Get the current state of the modem."""
        modem_state = self.get_mm_modem().get_state()
        return ModemManager.ModemState.get_string(modem_state)

    def lte_up(self, connection_name):
        """LTE Up."""
        # Find the connection
        connections = NetworkManager.Settings.ListConnections()
        connections = dict([(x.GetSettings()['connection']['id'], x) for x in connections])
        conn = connections[connection_name]
# TODO: check for non null

        # Find a suitable device
        ctype = conn.GetSettings()['connection']['type']
        if ctype == 'vpn':
            for dev in NetworkManager.NetworkManager.GetDevices():
                if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED and dev.Managed:
                    break
            else:
                _LOGGER.error("No active, managed device %s found" % ctype)
                raise ModemGatewayException("No active, managed device %s found" % ctype)
        else:
            dtype = {
                '802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI,
                '802-3-ethernet': NetworkManager.NM_DEVICE_TYPE_ETHERNET,
                'gsm': NetworkManager.NM_DEVICE_TYPE_MODEM,
            }.get(ctype,ctype)
            devices = NetworkManager.NetworkManager.GetDevices()

            for dev in devices:
                if dev.DeviceType == dtype and dev.State == NetworkManager.NM_DEVICE_STATE_DISCONNECTED:
                    break
            else:
                _LOGGER.error("No suitable and available %s device found" % ctype)
                return

        # And connect
        NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")

    def lte_down(self):
        """LTE Down."""
        # list of devices with active connection
        devices = list(filter(lambda _device: _device.ActiveConnection is not None, NetworkManager.NetworkManager.GetAllDevices()))

        # print the list
        for index, device in enumerate(devices):
            print(index , ")" , device.Interface)

        if (devices):
            active_connection = devices[0].ActiveConnection
            print(active_connection.Id)
            NetworkManager.NetworkManager.DeactivateConnection(active_connection)
        else:
            _LOGGER.warning('No active LTE connection found')


def create_modem_gateway(config, hass):
    """Create the modem gateway."""
    gateway = Gateway(hass)
    return gateway
