"""Platform for sensor integration."""

import logging

from datetime import datetime

from .const import (
    DOMAIN,
    MODEM_GATEWAY,
    EVT_MODEM_CONNECTED,
    EVT_MODEM_DISCONNECTED,
    EVT_LTE_CONNECTED,
    EVT_LTE_DISCONNECTED,
    SENSOR_LASTUPDATE
)

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_SIGNAL = 'signal_strength'
SENSOR_STATUS = 'modem_status'
SENSOR_OPERATOR = 'cell_operator'
REGISTERED_STATUS = 'registered'
CONNECTED_STATUS = 'connected'
GSM_SENSOR_ID = 'mm_modem.signal_strength'
GSM_SENSOR_NAME = 'GSM Modem'
LTE_SENSOR_ID = 'mm_modem.lte_status'
LTE_SENSOR_NAME = 'LTE Connection'


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    add_entities([GsmModemSensor(hass)])
    add_entities([LteConnectionSensor(hass)])


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    async_add_entities([GsmModemSensor(hass)])
    async_add_entities([LteConnectionSensor(hass)])


class GsmModemSensor(BinarySensorEntity):
    """Representation of a Sensor."""
    _signal_strength = 0
    _modem_status = 'none'
    _cell_operator = 'none'
    _hass = None
    _prev_status = False

    def __init__(self, hass):
        """Initialize the sensor."""
        self._state = None
        self._hass = hass
        hass.bus.async_listen(EVT_MODEM_DISCONNECTED,
                              self._handle_modem_disconnected)

        hass.bus.async_listen(EVT_MODEM_CONNECTED,
                              self._handle_modem_connected)
        self.update()

    async def _handle_modem_disconnected(self, call):
        self.update()
        self.async_write_ha_state()

    async def _handle_modem_connected(self, call):
        self.update()
        self.async_write_ha_state()

    def get_gateway(self):
        """Returns the modem gateway instance from hass scope"""
        return self._hass.data[DOMAIN][MODEM_GATEWAY]

    @property
    def name(self):
        """Return the name of the sensor."""
        return GSM_SENSOR_NAME

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return [REGISTERED_STATUS,
                CONNECTED_STATUS].__contains__(self._modem_status)

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def unique_id(self):
        """Return a unique ID."""
        return GSM_SENSOR_ID

    @property
    def device_state_attributes(self):
        """Return device specific state attributes.
        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        return {SENSOR_STATUS: self._modem_status,
                SENSOR_OPERATOR: self._cell_operator,
                SENSOR_SIGNAL: self._signal_strength,
                SENSOR_LASTUPDATE: datetime.strptime(datetime.now(),
                                                     '%Y-%m-%dT%H:%M:%S')}

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        gateway = self.get_gateway()
        modem_info = gateway.get_modem_state()
        if modem_info is not None:
            self._signal_strength = modem_info['signal']
            self._cell_operator = modem_info['operator']
            self._modem_status = modem_info['status']
            if not self._prev_status:
                self._prev_status = True
                _LOGGER.info('GSM modem connected')
        else:
            self._signal_strength = 0
            self._modem_status = 'none'
            self._cell_operator = 'none'
            if self._prev_status:
                self._prev_status = False
                _LOGGER.info('GSM modem disconnected')


class LteConnectionSensor(BinarySensorEntity):
    """Representation of a Sensor."""
    _modem_status = None
    _hass = None
    _prev_status = False

    def __init__(self, hass):
        """Initialize the sensor."""
        self._state = None
        self._hass = hass
        hass.bus.async_listen(EVT_LTE_DISCONNECTED,
                              self._handle_lte_disconnected)

        hass.bus.async_listen(EVT_LTE_CONNECTED,
                              self._handle_lte_connected)

    async def _handle_lte_disconnected(self, call):
        self.update()
        self.async_write_ha_state()

    async def _handle_lte_connected(self, call):
        self.update()
        self.async_write_ha_state()

    def get_gateway(self):
        """Returns the modem gateway instance from hass scope"""
        return self._hass.data[DOMAIN][MODEM_GATEWAY]

    @property
    def name(self):
        """Return the name of the sensor."""
        return LTE_SENSOR_NAME

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return [CONNECTED_STATUS].__contains__(self._modem_status)

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def unique_id(self):
        """Return a unique ID."""
        return LTE_SENSOR_ID

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
        modem_info = gateway.get_modem_state()
        if modem_info is not None:
            self._modem_status = modem_info['status']
        else:
            self._modem_status = 'none'
