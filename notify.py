# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Support for SMS notification services."""

import logging

import voluptuous as vol

from homeassistant.components.notify import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_RECIPIENT
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, MODEM_GATEWAY
from .exceptions import GSMGatewayException

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RECIPIENT): cv.string,
        vol.Optional(CONF_NAME): cv.string,
    }
)


def get_sms_service(hass):
    """Get the SMS notification service."""
    domain_data = hass.data.get(DOMAIN, {})
    gateway = domain_data.get(MODEM_GATEWAY) if isinstance(domain_data, dict) else None
    if gateway is None:
        _LOGGER.error("GSM gateway not found, cannot initialize service")
        raise GSMGatewayException("GSM gateway not found")

    return SMSNotificationService(gateway, hass)


class SMSNotificationService:
    """Implement the notification service for SMS."""

    def __init__(self, gateway, hass=None):
        """Initialize the service."""
        self.gateway = gateway
        self.hass = hass

    def send_message(self, number, message):
        """Send SMS message."""
        self.gateway.send_sms(number, message)

    async def delete_message(self, path):
        """Delete SMS message."""
        await self.gateway.delete_sms_message(path)
