"""The sms component."""

import sys, signal, gi

gi.require_version('ModemManager', '1.0')
from gi.repository import GLib, GObject, Gio, ModemManager

import logging

import voluptuous as vol

from homeassistant.core import callback

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .const import (
    DOMAIN,
    MODEM_GATEWAY,
    ATTR_PHONE_NUMBER,
    ATTR_MESSAGE,
    ATTR_CONNECTION_NAME,
    ATTR_SMS_PATH
)

from .gateway import create_modem_gateway
from .notify import get_sms_service
from .dialer import get_dialer_service
from .lte import get_lte_service


MM_SEND_SMS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PHONE_NUMBER): cv.string,
        vol.Required(ATTR_MESSAGE): cv.string,
    }
)

MM_DELETE_SMS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SMS_PATH): cv.string,
    }
)

MM_DIAL_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PHONE_NUMBER): cv.string,
    }
)

MM_LTE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONNECTION_NAME): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def async_setup(hass, config):
    """Import integration from config."""

    if DOMAIN in config:
        _LOGGER.debug(config[DOMAIN])
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
    return True


async def async_setup_entry(hass, config_entry):
    """Set up the LTE Modem component."""

    @callback
    def handle_send_sms(call):
        """Handle the sms sending service call."""
        number = call.data.get(ATTR_PHONE_NUMBER)
        message = call.data.get(ATTR_MESSAGE)
        # Prepare SMS properties
        sms_properties = ModemManager.SmsProperties.new ()
        sms_properties.set_number(number)
        sms_properties.set_text(message)

        # Connection to ModemManager
        connection = Gio.bus_get_sync (Gio.BusType.SYSTEM, None)
        manager = ModemManager.Manager.new_sync (connection, Gio.DBusObjectManagerClientFlags.DO_NOT_AUTO_START, None)
        if manager.get_name_owner() is None:
            print('ModemManager not found in bus')

        # Iterate modems and send SMS with each
        for obj in manager.get_objects():
            messaging = obj.get_modem_messaging()
            sms = messaging.create_sync(sms_properties)
            sms.send_sync()
            print('%s: sms sent' % messaging.get_object_path()) 
#        sms_service = get_sms_service(hass)
#        sms_service.send_message(number, message)

    @callback
    async def handle_delete_sms(call):
        """Handle the sms deleting service call."""
        path = call.data.get(ATTR_SMS_PATH)
        sms_service = get_sms_service(hass)
        await sms_service.delete_message(path)

    @callback
    async def handle_dial(call):
        """Handle the sms sending service call."""
        number = call.data.get(ATTR_PHONE_NUMBER)
        dialer_service = get_dialer_service(hass)
        await dialer_service.dial(number)

    @callback
    async def handle_lte_up(call):
        """Handle the service call."""
        lte_service = get_lte_service(hass)
        await lte_service.lte_up()

    @callback
    async def handle_lte_down(call):
        """Handle the service call."""
        lte_service = get_lte_service(hass)
        await lte_service.lte_down()

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry,
                                                      "binary_sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry,
                                                      "sensor")
    )

    hass.data.setdefault(DOMAIN, {})

    gateway = create_modem_gateway(config_entry, hass)

    if not gateway:
        return False

    hass.data[DOMAIN][MODEM_GATEWAY] = gateway

    await gateway.async_added_to_hass()

    hass.services.async_register(DOMAIN,
                                 'send_sms',
                                 handle_send_sms,
                                 schema=MM_SEND_SMS_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN,
                                 'delete_sms',
                                 handle_delete_sms,
                                 schema=MM_DELETE_SMS_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN,
                                 'dial',
                                 handle_dial,
                                 schema=MM_DIAL_SERVICE_SCHEMA)

    hass.services.async_register(DOMAIN,
                                 'lte_up',
                                 handle_lte_up)

    hass.services.async_register(DOMAIN,
                                 'lte_down',
                                 handle_lte_down)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP,
                               gateway.stop_glib_loop)

    return True
