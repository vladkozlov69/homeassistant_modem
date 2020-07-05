"""The sms component."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, MODEM_GATEWAY
from .gateway import create_modem_gateway

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICE): cv.isdevice})},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Configure Gammu state machine."""
    hass.data.setdefault(DOMAIN, {})
    sms_config = config.get(DOMAIN, {})
    if not sms_config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=sms_config,
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configure Gammu state machine."""

    device = entry.data[CONF_DEVICE]
    config = {"Device": device, "Connection": "at"}
    gateway = await create_modem_gateway(config, hass)
    if not gateway:
        return False
    hass.data[DOMAIN][MODEM_GATEWAY] = gateway
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        gateway = hass.data[DOMAIN].pop(MODEM_GATEWAY)
        await gateway.terminate_async()

    return unload_ok
