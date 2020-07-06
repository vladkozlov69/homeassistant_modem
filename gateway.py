"""The sms gateway to interact with a GSM modem."""
import logging

import sys, signal, gi

gi.require_version('ModemManager', '1.0')
from gi.repository import GLib, GObject, Gio, ModemManager

from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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


    def send_sms_async(self, number, message):
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


def create_modem_gateway(config, hass):
    """Create the modem gateway."""
    gateway = Gateway(hass)
    return gateway
