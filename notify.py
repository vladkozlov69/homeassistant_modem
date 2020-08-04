"""Support for SMS notification services."""
import logging

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, MODEM_GATEWAY
from .exceptions import GSMGatewayException

_LOGGER = logging.getLogger(__name__)


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

    def send_message(self, number, message):
        """Send SMS message."""
        self.gateway.send_sms(number, message)
