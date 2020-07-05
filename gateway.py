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
        return get_mm_object().get_modem()


    async def send_sms_async(self, number, message):
        """Send sms message via the worker."""
        sms_properties = ModemManager.SmsProperties.new ()
        sms_properties.set_number(number)
        sms_properties.set_text(message)

        # Connection to ModemManager
        connection = Gio.bus_get_sync (Gio.BusType.SYSTEM, None)
        manager = ModemManager.Manager.new_sync (connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None)
        if manager.get_name_owner() is None:
            sys.stderr.write('ModemManager not found in bus')
            sys.exit(2)

        # Iterate modems and send SMS with each
        for obj in manager.get_objects():
            messaging = obj.get_modem_messaging()
            sms = messaging.create_sync(sms_properties)
            sms.send_sync()
            print('%s: sms sent' % messaging.get_object_path())
        return await self._worker.send_sms_async(message)


    async def get_operator_name_async(self):
        """Get the IMEI of the device."""
        return get_mm_modem().get_sim_sync().get_operator_name()


    async def get_signal_quality_async(self):
        """Get the current signal level of the modem."""
        return get_mm_modem().get_signal_quality()


async def create_modem_gateway(config, hass):
    """Create the modem gateway."""
    gateway = Gateway(hass)
    return gateway
