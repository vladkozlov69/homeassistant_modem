# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Support for Dial notification services."""

import logging

from .exceptions import GSMGatewayException
from .gateway import get_modem_gateway

_LOGGER = logging.getLogger(__name__)


def get_dialer_service(hass):
    """Get the dialer service."""
    return DialerNotificationService(get_modem_gateway(hass), hass)


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
