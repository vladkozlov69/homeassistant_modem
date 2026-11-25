# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""The sms component."""

from collections.abc import Mapping
import logging

import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv, discovery

from .const import (
    ATTR_CONNECTION_NAME,
    ATTR_MESSAGE,
    ATTR_PHONE_NUMBER,
    ATTR_SMS_PATH,
    DOMAIN,
    EVT_SMS_FORGET,
    MODEM_GATEWAY,
)
from .dialer import get_dialer_service
from .gateway import create_modem_gateway, get_modem_gateway
from .lte import get_lte_service
from .notify import get_sms_service

MM_SEND_SMS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PHONE_NUMBER): cv.string,
        vol.Required(ATTR_MESSAGE): cv.string,
    }
)

MM_DELETE_SMS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SMS_PATH): cv.string,
    }
)

MM_DIAL_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PHONE_NUMBER): cv.string,
    }
)

MM_LTE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONNECTION_NAME): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the modem integration from YAML config."""
    conf = config.get(DOMAIN)
    if conf is None:
        _LOGGER.debug("No config for %s, skipping setup.", DOMAIN)
        return True

    domain_data = hass.data.setdefault(DOMAIN, {})
    if not isinstance(domain_data, dict):
        domain_data = {}
        hass.data[DOMAIN] = domain_data
    if isinstance(conf, Mapping):
        domain_data["config"] = conf

    await async_setup_modem(hass, conf)

    _LOGGER.debug("Loading sensor and binary_sensor platforms")
    await discovery.async_load_platform(hass, "sensor", DOMAIN, conf, config)
    await discovery.async_load_platform(hass, "binary_sensor", DOMAIN, conf, config)
    return True


async def async_setup_modem(hass, config_entry):
    """Set up the LTE Modem component."""

    async def handle_send_sms(call):
        """Handle the sms sending service call."""
        number = call.data.get(ATTR_PHONE_NUMBER)
        message = call.data.get(ATTR_MESSAGE)
        gateway = get_modem_gateway(hass)
        await hass.async_add_executor_job(gateway.send_sms, number, message)

    async def handle_delete_sms(call):
        """Handle the sms deleting service call."""
        path = call.data.get(ATTR_SMS_PATH)
        sms_service = get_sms_service(hass)
        await sms_service.delete_message(path)

    async def handle_dial(call):
        """Handle the voice dial service call."""
        number = call.data.get(ATTR_PHONE_NUMBER)
        dialer_service = get_dialer_service(hass)
        await dialer_service.dial(number)

    async def handle_lte_up(call):
        """Handle the LTE up service call."""
        lte_service = get_lte_service(hass)
        await lte_service.lte_up(call.data.get(ATTR_CONNECTION_NAME))

    async def handle_lte_down(call):
        """Handle the LTE down service call."""
        lte_service = get_lte_service(hass)
        await lte_service.lte_down(call.data.get(ATTR_CONNECTION_NAME))

    @callback
    def handle_sms_forget(call):
        """Handle the sms forgetting service call."""
        _LOGGER.debug("Firing event: %s", EVT_SMS_FORGET)
        hass.bus.async_fire_internal(EVT_SMS_FORGET)

    domain_data = hass.data.setdefault(DOMAIN, {})
    if not isinstance(domain_data, dict):
        domain_data = {}
        hass.data[DOMAIN] = domain_data

    modem_gateway = create_modem_gateway(config_entry, hass)
    if not modem_gateway:
        return False

    domain_data[MODEM_GATEWAY] = modem_gateway
    await modem_gateway.async_added_to_hass()

    hass.services.async_register(
        DOMAIN, "send_sms", handle_send_sms, schema=MM_SEND_SMS_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "delete_sms", handle_delete_sms, schema=MM_DELETE_SMS_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "dial", handle_dial, schema=MM_DIAL_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "lte_up", handle_lte_up, schema=MM_LTE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "lte_down", handle_lte_down, schema=MM_LTE_SERVICE_SCHEMA
    )
    hass.services.async_register(DOMAIN, "sms_forget", handle_sms_forget)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, modem_gateway.stop_glib_loop)

    return True
