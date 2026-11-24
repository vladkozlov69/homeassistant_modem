# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Support for Dial notification services."""

import logging

from .const import DOMAIN, MODEM_GATEWAY
from .exceptions import GSMGatewayException

_LOGGER = logging.getLogger(__name__)


def get_dialer_service(hass):
    """Get the dialer service."""
    domain_data = hass.data.get(DOMAIN, {})
    gateway = domain_data.get(MODEM_GATEWAY) if isinstance(domain_data, dict) else None
    if gateway is None:
        _LOGGER.error("GSM gateway not found, cannot initialize service")
        raise GSMGatewayException("GSM gateway not found")

    return DialerNotificationService(gateway, hass)


class DialerNotificationService:
    """Implement the notification service for Dialer."""

    def __init__(self, gateway, hass=None):
        """Initialize the service."""
        self.gateway = gateway
        self.hass = hass

    async def dial(self, number):
        """Dial the given number."""
        if self.hass is not None:
            await self.hass.async_add_executor_job(self.gateway.dial_voice, number)
        else:
            self.gateway.dial_voice(number)
