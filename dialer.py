"""Support for Dial notification services."""
import logging

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, MODEM_GATEWAY
from .exceptions import GSMGatewayException

_LOGGER = logging.getLogger(__name__)


def get_dialer_service(hass):
    """Get the SMS notification service."""

    if MODEM_GATEWAY not in hass.data[DOMAIN]:
        _LOGGER.error("SMS gateway not found, cannot initialize service")
        raise GSMGatewayException("GSM gateway not found")

    gateway = hass.data[DOMAIN][MODEM_GATEWAY]

    return DialerNotificationService(gateway)


class DialerNotificationService:
    """Implement the notification service for Dialer."""

    def __init__(self, gateway):
        """Initialize the service."""
        self.gateway = gateway

    def dial(self, number):
        """Dial the given number."""

        self.gateway.dial_voice(number)
