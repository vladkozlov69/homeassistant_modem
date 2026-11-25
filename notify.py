# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Support for SMS notification services."""

import logging

import voluptuous as vol

from homeassistant.components.notify import (
    ATTR_TARGET,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from homeassistant.const import CONF_NAME, CONF_RECIPIENT
from homeassistant.helpers import config_validation as cv

from .gateway import get_modem_gateway

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RECIPIENT): cv.string,
        vol.Optional(CONF_NAME): cv.string,
    }
)


async def async_get_service(hass, config, discovery_info=None):
    """Get the SMS notification service for Home Assistant's notify platform."""
    gateway = get_modem_gateway(hass)
    return SMSNotificationService(
        gateway, hass, default_recipient=config.get(CONF_RECIPIENT)
    )


def get_sms_service(hass):
    """Get the SMS notification service."""
    return SMSNotificationService(get_modem_gateway(hass), hass)


class SMSNotificationService(BaseNotificationService):
    """Implement the notification service for SMS."""

    def __init__(self, gateway, hass=None, default_recipient=None):
        """Initialize the service."""
        self.gateway = gateway
        self.hass = hass
        self._default_recipient = default_recipient

    async def send_message(self, message="", **kwargs):
        """Send an SMS message to target numbers or the configured recipient."""
        targets = kwargs.get(ATTR_TARGET)
        if not targets:
            if not self._default_recipient:
                _LOGGER.error("No SMS recipient specified")
                return
            targets = [self._default_recipient]

        if self.hass is not None:
            for target in targets:
                await self.hass.async_add_executor_job(self.gateway.send_sms, target, message)
        else:
            for target in targets:
                self.gateway.send_sms(target, message)

    async def delete_message(self, path):
        """Delete SMS message."""
        await self.gateway.delete_sms_message(path)
