"""Support for SMS notification services."""
import logging

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, MODEM_GATEWAY

_LOGGER = logging.getLogger(__name__)

def get_lte_service(hass):
    """Get the SMS notification service."""

    if MODEM_GATEWAY not in hass.data[DOMAIN]:
        _LOGGER.error("SMS gateway not found, cannot initialize service")
        return

    gateway = hass.data[DOMAIN][MODEM_GATEWAY]

    return MMLteService(gateway)


class MMLteService:
    """Implement the notification service for SMS."""

    def __init__(self, gateway):
        """Initialize the service."""
        self.gateway = gateway

    def lte_up(self):
        """LTE Up."""
        self.gateway.lte_up()

    def lte_down(self):
        """LTE Down."""
        self.gateway.lte_down()
