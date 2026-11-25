# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Platform for sensor integration."""

from collections.abc import Mapping
import logging

from homeassistant.components import logbook
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import Event
from homeassistant.util import dt as dt_util

from .const import (
    CONF_REMOVE_INCOMING_SMS,
    DOMAIN,
    EVT_SMS_DELETE,
    EVT_SMS_FORGET,
    EVT_SMS_RECEIVED,
    MODEM_GATEWAY,
    SENSOR_LASTUPD,
    SMS_SENSOR_ID,
    SMS_SENSOR_NAME,
)

_LOGGER = logging.getLogger(__name__)
_MAX_SEEN_SMS = 500


def _remember(cache: dict, key: str, maxlen: int = _MAX_SEEN_SMS) -> None:
    """Insert key into a bounded insertion-ordered dict."""
    if key not in cache and len(cache) >= maxlen:
        cache.pop(next(iter(cache)))
    cache[key] = None


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    async_add_entities([GsmModemSmsSensor(hass, config_entry)])


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the modem sensor from YAML."""
    conf = discovery_info if discovery_info is not None else config
    add_entities([GsmModemSmsSensor(hass, conf)])


class GsmModemSmsSensor(SensorEntity):
    """Representation of an incoming SMS count sensor."""

    def __init__(self, hass, conf_entry):
        """Initialize the sensor."""
        self._state = None
        self._lastupdate = dt_util.now()
        self._hass = hass
        self._messages = []
        self._remove_inc_sms = self._read_remove_incoming_sms(conf_entry)
        self._processed_messages = {}
        self._duplicated_content = {}
        self._unsub_listeners = []
        self._unsub_listeners.append(
            hass.bus.async_listen(EVT_SMS_RECEIVED, self._handle_sms_received)
        )
        self._unsub_listeners.append(
            hass.bus.async_listen(EVT_SMS_FORGET, self._handle_sms_forget)
        )
        self._unsub_listeners.append(
            hass.bus.async_listen(EVT_SMS_DELETE, self._handle_sms_delete)
        )
        _LOGGER.debug("Sms sensor up")

    @staticmethod
    def _read_remove_incoming_sms(conf_entry):
        """Read remove_incoming_sms from mapping or config-entry-like object."""
        if conf_entry is None:
            return False
        if isinstance(conf_entry, Mapping):
            return bool(conf_entry.get(CONF_REMOVE_INCOMING_SMS, False))
        data = getattr(conf_entry, "data", None)
        if isinstance(data, Mapping) and CONF_REMOVE_INCOMING_SMS in data:
            return bool(data.get(CONF_REMOVE_INCOMING_SMS, False))
        options = getattr(conf_entry, "options", None)
        if isinstance(options, Mapping):
            return bool(options.get(CONF_REMOVE_INCOMING_SMS, False))
        return False

    def get_gateway(self):
        """Return the modem gateway instance from hass scope."""
        domain_data = self._hass.data.get(DOMAIN)
        if isinstance(domain_data, Mapping):
            return domain_data.get(MODEM_GATEWAY)
        return None

    @property
    def name(self):
        """Return the name of the sensor."""
        return SMS_SENSOR_NAME

    @property
    def unique_id(self):
        """Return a unique ID."""
        return SMS_SENSOR_ID

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {SENSOR_LASTUPD: self._lastupdate.strftime("%Y-%m-%dT%H:%M:%S")}

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return True

    async def async_will_remove_from_hass(self):
        """Clean up event listeners."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    async def _handle_sms_received(self, call):
        await self.async_update()
        self.async_write_ha_state()

    async def _handle_sms_forget(self, call):
        self._processed_messages.clear()
        self._duplicated_content.clear()
        _LOGGER.debug("[_handle_sms_forget] Cleared processed_messages list")
        await self._handle_sms_received(call)

    async def _handle_sms_delete(self, call: Event):
        message_path = call.data.get("path")
        if message_path is None:
            _LOGGER.error("No message path specified for %s", EVT_SMS_DELETE)
            return
        _LOGGER.debug("_handle_sms_delete: %s", message_path)
        gateway = self.get_gateway()
        if gateway is None:
            _LOGGER.error("Gateway not available, cannot delete SMS %s", message_path)
            return
        await gateway.delete_sms_message(message_path)

    async def async_update(self):
        """Fetch new state data for the sensor."""
        gateway = self.get_gateway()
        self._lastupdate = dt_util.now()
        if gateway is None:
            self._state = None
            self._messages = []
            return

        get_messages = gateway.get_sms_messages
        executor_job = getattr(self._hass, "async_add_executor_job", None)
        if executor_job is None:
            messages = get_messages()
        else:
            result = executor_job(get_messages)
            if hasattr(result, "__await__"):
                messages = await result
            else:
                messages = result
        if messages is None:
            self._state = None
            self._messages = []
            return

        self._messages = messages
        self._state = len(self._messages)
        if len(self._messages) == 0:
            return

        _LOGGER.debug("[update] CONF_REMOVE_INCOMING_SMS: %s", self._remove_inc_sms)
        _LOGGER.debug("[update] Messages count: %s", len(self._messages))

        for message in self._messages:
            message_content = (
                f"{message.number}|{message.text}|{message.timestamp}"
            )
            if (
                message.path not in self._processed_messages
                and message_content not in self._duplicated_content
            ):
                _LOGGER.debug(message.path)
                _remember(self._processed_messages, message.path)
                _remember(self._duplicated_content, message_content)

                logbook.async_log_entry(
                    self._hass,
                    SMS_SENSOR_NAME,
                    message.text,
                    DOMAIN,
                    SMS_SENSOR_ID,
                )

                _LOGGER.debug(
                    "[update] Firing event: %s_incoming_sms for %s",
                    DOMAIN,
                    message.path,
                )
                self._hass.bus.async_fire(
                    event_type=DOMAIN + "_incoming_sms",
                    event_data={
                        "path": message.path,
                        "number": message.number,
                        "timestamp": message.timestamp,
                        "text": message.text,
                    },
                )
            else:
                _LOGGER.debug("[update] Skipping as already processed: %s", message.path)

            if self._remove_inc_sms:
                await gateway.delete_sms_message(message.path)
