"""Support for SMS notification services."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, MODEM_GATEWAY
from .exceptions import GSMGatewayException

from homeassistant.components.notify import PLATFORM_SCHEMA

from homeassistant.const import CONF_NAME, CONF_RECIPIENT

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RECIPIENT): cv.string,
        vol.Optional(CONF_NAME): cv.string
    }
)


def get_sms_service(hass):
    """Get the SMS notification service."""

    if MODEM_GATEWAY not in hass.data[DOMAIN]:
        _LOGGER.error("GSM gateway not found, cannot initialize service")
        raise GSMGatewayException("GSM gateway not found")

    gateway = hass.data[DOMAIN][MODEM_GATEWAY]

    return SMSNotificationService(gateway)


class SMSNotificationService:
    """Implement the notification service for SMS."""

    def __init__(self, gateway):
        """Initialize the service."""
        self.gateway = gateway

    async def send_message(self, number, message):
        """Send SMS message."""
        self.gateway.send_sms(number, message)

    async def delete_message(self, path):
        """Send SMS message."""
        self.gateway.delete_sms_message(path)
