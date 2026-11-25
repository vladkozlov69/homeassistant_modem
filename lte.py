# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Support for LTE control services."""

import logging

from .gateway import get_modem_gateway

_LOGGER = logging.getLogger(__name__)


def get_lte_service(hass):
    """Get the LTE service."""
    return MMLteService(get_modem_gateway(hass), hass)


class MMLteService:
    """Implement the LTE control service."""

    def __init__(self, gateway, hass=None):
        """Initialize the service."""
        self.gateway = gateway
        self.hass = hass

    async def lte_up(self, connection_name=None):
        """LTE Up."""
        if self.hass is not None:
            await self.hass.async_add_executor_job(self.gateway.lte_up, connection_name)
        else:
            self.gateway.lte_up(connection_name)

    async def lte_down(self, connection_name=None):
        """LTE Down."""
        if self.hass is not None:
            await self.hass.async_add_executor_job(self.gateway.lte_down, connection_name)
        else:
            self.gateway.lte_down(connection_name)
