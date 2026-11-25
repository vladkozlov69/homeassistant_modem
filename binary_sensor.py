# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

"""Platform for binary sensor integration."""

from collections.abc import Mapping
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    EVT_LTE_CONNECTED,
    EVT_LTE_DISCONNECTED,
    EVT_MODEM_CONNECTED,
    EVT_MODEM_DISCONNECTED,
    MODEM_GATEWAY,
    SENSOR_LASTUPD,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_SIGNAL = "signal_strength"
SENSOR_STATUS = "modem_status"
SENSOR_OPERATOR = "cell_operator"
REGISTERED_STATUS = "registered"
CONNECTED_STATUS = "connected"
GSM_SENSOR_ID = "mm_modem.signal_strength"
GSM_SENSOR_NAME = "GSM Modem"
LTE_SENSOR_ID = "mm_modem.lte_status"
LTE_SENSOR_NAME = "LTE Connection"


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([GsmModemSensor(hass), LteConnectionSensor(hass)])


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    async_add_entities([GsmModemSensor(hass), LteConnectionSensor(hass)])


class _BaseModemBinarySensor(BinarySensorEntity):
    """Shared base class for modem connectivity binary sensors."""

    def __init__(self, hass):
        """Initialize shared entity state."""
        self.hass = hass
        self._unsub_listeners = []

    async def async_added_to_hass(self):
        """Refresh initial state when entity is added."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Clean up event listeners."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    async def _async_update_state(self):
        """Run synchronous update in executor when available."""
        executor_job = getattr(self.hass, "async_add_executor_job", None)
        if executor_job is None:
            self.update()
            return
        result = executor_job(self.update)
        if hasattr(result, "__await__"):
            await result

    def get_gateway(self):
        """Return the modem gateway instance from hass scope."""
        domain_data = self.hass.data.get(DOMAIN)
        if isinstance(domain_data, Mapping):
            return domain_data.get(MODEM_GATEWAY)
        return None

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return BinarySensorDeviceClass.CONNECTIVITY


class GsmModemSensor(_BaseModemBinarySensor):
    """Representation of a GSM modem connectivity sensor."""

    def __init__(self, hass):
        """Initialize the sensor."""
        super().__init__(hass)
        self._signal_strength = 0
        self._modem_status = "none"
        self._cell_operator = "none"
        self._prev_status = False
        self._unsub_listeners.append(
            hass.bus.async_listen(EVT_MODEM_DISCONNECTED, self._handle_modem_disconnected)
        )
        self._unsub_listeners.append(
            hass.bus.async_listen(EVT_MODEM_CONNECTED, self._handle_modem_connected)
        )

    async def _handle_modem_disconnected(self, call):
        _LOGGER.info("_handle_modem_disconnected")
        await self._async_update_state()
        self.async_write_ha_state()

    async def _handle_modem_connected(self, call):
        _LOGGER.info("_handle_modem_connected")
        await self._async_update_state()
        self.async_write_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return GSM_SENSOR_NAME

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._modem_status in (REGISTERED_STATUS, CONNECTED_STATUS)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return GSM_SENSOR_ID

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            SENSOR_STATUS: self._modem_status,
            SENSOR_OPERATOR: self._cell_operator,
            SENSOR_SIGNAL: self._signal_strength,
            SENSOR_LASTUPD: dt_util.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def update(self):
        """Fetch new state data for the sensor."""
        gateway = self.get_gateway()
        if gateway is None:
            modem_info = None
        else:
            try:
                modem_info = gateway.get_modem_state()
            except Exception:  # pragma: no cover - backend dependent
                _LOGGER.exception("Failed to read modem state")
                modem_info = None

        if modem_info is not None:
            self._signal_strength = modem_info.get("signal", 0)
            self._cell_operator = modem_info.get("operator", "none")
            self._modem_status = modem_info.get("status", "none")
            if not self._prev_status:
                self._prev_status = True
                _LOGGER.info("GSM modem connected")
        else:
            self._signal_strength = 0
            self._modem_status = "none"
            self._cell_operator = "none"
            if self._prev_status:
                self._prev_status = False
                _LOGGER.info("GSM modem disconnected")


class LteConnectionSensor(_BaseModemBinarySensor):
    """Representation of an LTE connection sensor."""

    def __init__(self, hass):
        """Initialize the sensor."""
        super().__init__(hass)
        self._lte_status = False
        self._modem_status = "none"
        self._unsub_listeners.append(
            hass.bus.async_listen(EVT_LTE_DISCONNECTED, self._handle_lte_disconnected)
        )
        self._unsub_listeners.append(
            hass.bus.async_listen(EVT_LTE_CONNECTED, self._handle_lte_connected)
        )

    async def _handle_lte_disconnected(self, call):
        await self._async_update_state()
        self.async_write_ha_state()

    async def _handle_lte_connected(self, call):
        await self._async_update_state()
        self.async_write_ha_state()

    @property
    def name(self):
        """Return the name of the sensor."""
        return LTE_SENSOR_NAME

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return bool(self._lte_status) or self._modem_status == CONNECTED_STATUS

    @property
    def unique_id(self):
        """Return a unique ID."""
        return LTE_SENSOR_ID

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {}

    def update(self):
        """Fetch new state data for the sensor."""
        gateway = self.get_gateway()
        if gateway is None:
            self._lte_status = False
            self._modem_status = "none"
            return

        try:
            self._lte_status = bool(gateway.get_lte_state())
        except Exception:  # pragma: no cover - backend dependent
            _LOGGER.exception("Failed to read LTE state")
            self._lte_status = False

        try:
            modem_info = gateway.get_modem_state()
        except Exception:  # pragma: no cover - backend dependent
            _LOGGER.exception("Failed to read modem state for LTE sensor")
            modem_info = None

        if modem_info is not None:
            self._modem_status = modem_info.get("status", "none")
        else:
            self._modem_status = "none"
