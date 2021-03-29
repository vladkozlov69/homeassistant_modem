"""Platform for sensor integration."""

import logging

from .const import DOMAIN, MODEM_GATEWAY, CONF_REMOVE_INCOMING_SMS

from homeassistant.helpers.entity import Entity

from homeassistant.components import logbook

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

SENSOR_ID = 'mm_modem.incoming_sms'
SENSOR_NAME = 'GSM Modem SMS'


# def setup_platform(hass, config, add_entities, discovery_info=None):
#     """Set up the sensor platform."""
#     _LOGGER.warn(config.data)
#     add_entities([GsmModemSmsSensor(hass)])


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    _LOGGER.info(config_entry.data)
    async_add_entities([GsmModemSmsSensor(hass, config_entry)])


class GsmModemSmsSensor(Entity):
    """Representation of a Sensor."""
    _hass = None

    def __init__(self, hass, conf_entry):
        """Initialize the sensor."""
        self._state = None
        self._hass = hass
        self._messages = []
        if CONF_REMOVE_INCOMING_SMS in conf_entry.data:
            self._remove_inc_sms = conf_entry.data[CONF_REMOVE_INCOMING_SMS]
        else:
            self._remove_inc_sms = False
        self._processed_messages = set()

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
        if messages is None:
            self._state = 'Unknown'
        else:
            self._messages = messages
            self._state = len(self._messages)
            _LOGGER.info('CONF_REMOVE_INCOMING_SMS:' + self._remove_inc_sms)
            for message in self._messages:
                if message.path not in self._processed_messages:
                    _LOGGER.info(message.path)
                    self._processed_messages.update({message.path})
                    _LOGGER.info(self._processed_messages)
                    self._hass.services.call(logbook.DOMAIN, 'log', {
                                            logbook.ATTR_NAME: SENSOR_NAME,
                                            logbook.ATTR_MESSAGE: message.text,
                                            logbook.ATTR_DOMAIN: DOMAIN,
                                            logbook.ATTR_ENTITY_ID: SENSOR_ID
                                            }, True)
                    self._hass.bus.async_fire(DOMAIN + '_incoming_sms',
                                              {'path': message.path,
                                               'number': message.number,
                                               'timestamp': message.timestamp,
                                               'text': message.text})
                    gateway.delete_sms_message(message.path)
