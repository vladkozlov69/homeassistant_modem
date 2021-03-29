"""Platform for sensor integration."""

import logging

from .const import DOMAIN, MODEM_GATEWAY

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    SensorEntity,
)

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


class GsmModemSmsSensor(SensorEntity):
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
        return {}

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = 777
        # gateway = self.get_gateway()
        # modem_info = gateway.get_modem_state()
        # if modem_info is not None:
        #     self._signal_strength = modem_info['signal']
        #     self._cell_operator = modem_info['operator']
        #     self._modem_status = modem_info['status']
        #     if not self._prev_status:
        #         self._prev_status = True
        #         _LOGGER.info('GSM modem connected')
        # else:
        #     self._signal_strength = 0
        #     self._modem_status = 'none'
        #     self._cell_operator = 'none'
        #     if self._prev_status:
        #         self._prev_status = False
        #         _LOGGER.info('GSM modem disconnected')
