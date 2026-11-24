"""Support for LTE control services."""

import logging

from .const import DOMAIN, MODEM_GATEWAY
from .exceptions import GSMGatewayException

_LOGGER = logging.getLogger(__name__)


def get_lte_service(hass):
    """Get the LTE service."""
    domain_data = hass.data.get(DOMAIN, {})
    gateway = domain_data.get(MODEM_GATEWAY) if isinstance(domain_data, dict) else None
    if gateway is None:
        _LOGGER.error("GSM gateway not found, cannot initialize service")
        raise GSMGatewayException("GSM gateway not found")

    return MMLteService(gateway, hass)


class MMLteService:
    """Implement the LTE control service."""

    def __init__(self, gateway, hass=None):
        """Initialize the service."""
        self.gateway = gateway
        self.hass = hass

    async def lte_up(self):
        """LTE Up."""
        if self.hass is not None:
            await self.hass.async_add_executor_job(self.gateway.lte_up)
        else:
            self.gateway.lte_up()

    async def lte_down(self):
        """LTE Down."""
        if self.hass is not None:
            await self.hass.async_add_executor_job(self.gateway.lte_down)
        else:
            self.gateway.lte_down()
