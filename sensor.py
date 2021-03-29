"""Platform for sensor integration."""

import logging

from .const import DOMAIN, MODEM_GATEWAY

from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

SENSOR_ID = 'mm_modem.incoming_sms'
SENSOR_NAME = 'GSM Modem SMS'


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([GsmModemSmsSensor(hass)])


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    async_add_entities([GsmModemSmsSensor(hass)])


class GsmModemSmsSensor(Entity):
    """Representation of a Sensor."""
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
    def unique_id(self):
        """Return a unique ID."""
        return SENSOR_ID

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes.
        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        return {}

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        gateway = self.get_gateway()
        messages = gateway.get_sms_messages()
        self._state = len(messages)
