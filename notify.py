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


# def get_service(hass, config, discovery_info=None):
#     """Get the SMS notification service."""

#     if MODEM_GATEWAY not in hass.data[DOMAIN]:
#         _LOGGER.error("SMS gateway not found, cannot initialize service")
#         return

#     gateway = hass.data[DOMAIN][MODEM_GATEWAY]

#     if discovery_info is None:
#         number = config[CONF_RECIPIENT]
#     else:
#         number = discovery_info[CONF_RECIPIENT]

#     return SMSNotificationService2(gateway, number)


def get_sms_service(hass):
    """Get the SMS notification service."""

    if MODEM_GATEWAY not in hass.data[DOMAIN]:
        _LOGGER.error("GSM gateway not found, cannot initialize service")
        raise GSMGatewayException("GSM gateway not found")

    gateway = hass.data[DOMAIN][MODEM_GATEWAY]

    return SMSNotificationService(gateway)


# class SMSNotificationService2(BaseNotificationService):
#     """Implement the notification service for SMS."""

#     def __init__(self, gateway, number):
#         """Initialize the service."""
#         self.gateway = gateway
#         self.number = number

#     async def async_send_message(self, message="", **kwargs):
#         """Send SMS message."""
#         try:
#             # Actually send the message
#             self.gateway.send_sms(self.number, message)
#         except GSMGatewayException as exc:
#             _LOGGER.error("Sending to %s failed: %s", self.number, exc)


class SMSNotificationService:
    """Implement the notification service for SMS."""

    def __init__(self, gateway):
        """Initialize the service."""
        self.gateway = gateway

    async def send_message(self, number, message):
        """Send SMS message."""
        self.gateway.send_sms(number, message)
