"""Platform for sensor integration."""

from homeassistant.helpers.entity import Entity
from datetime import timedelta
import logging

from random import randrange

from .const import DOMAIN, MODEM_GATEWAY

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_SIGNAL = 'signal_strength'
SENSOR_STATUS = 'modem_status'
SENSOR_OPERATOR = 'cell_operator'
REGISTERED_STATUS = 'registered'
SENSOR_ID = 'mm_modem.signal_strength'
SENSOR_NAME = 'GSM Modem'


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([GsmModemSensor(hass)])


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Speedtestdotnet sensors."""
    async_add_entities([GsmModemSensor(hass)])


class GsmModemSensor(BinarySensorEntity):
    """Representation of a Sensor."""
    _signal_strength = 0
    _modem_status = 'none'
    _cell_operator = 'none'
    _hass = None

    def __init__(self, hass):
        """Initialize the sensor."""
        self._state = None
        self._hass = hass

    def get_gateway(self):
        """Returns the modem gateway instance from hass scope"""
        return self._hass.data[DOMAIN][MODEM_GATEWAY]

    @property
    def name(self):
        """Return the name of the sensor."""
        return SENSOR_NAME

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return REGISTERED_STATUS == self._modem_status

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def unique_id(self):
        """Return a unique ID."""
        return SENSOR_ID

    @property
    def device_state_attributes(self):
        """Return device specific state attributes.
        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        return {SENSOR_STATUS: self._modem_status,
                SENSOR_OPERATOR: self._cell_operator,
                SENSOR_SIGNAL: self._signal_strength}

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        gateway = self.get_gateway()

        self._signal_strength = gateway.get_signal_strength()
        self._cell_operator = gateway.get_operator_name()
        self._modem_status = gateway.get_modem_state()
