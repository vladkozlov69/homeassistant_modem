"""The sms component."""
import asyncio
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, MODEM_GATEWAY, ATTR_PHONE_NUMBER, ATTR_MESSAGE
from .gateway import create_modem_gateway
from .notify import get_service


MM_SMS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PHONE_NUMBER): cv.string,
        vol.Required(ATTR_MESSAGE): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    def handle_send_sms(call):
        """Handle the service call."""

        number = call.data.get(ATTR_PHONE_NUMBER)
        message = call.data.get(ATTR_MESSAGE)
        get_service(hass).send_message("067683837", "HA")

    hass.data.setdefault(DOMAIN, {})

    _LOGGER.info("Before create_modem_gateway")

    gateway = create_modem_gateway(config, hass)

    _LOGGER.info("After create_modem_gateway")

    if not gateway:
        return False
    hass.data[DOMAIN][MODEM_GATEWAY] = gateway

    hass.services.register(DOMAIN, 'send_sms', handle_send_sms, schema=MM_SMS_SERVICE_SCHEMA)


    # Return boolean to indicate that initialization was successfully.
    return True
