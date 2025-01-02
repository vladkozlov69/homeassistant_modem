"""Platform for sensor integration."""

import logging

from datetime import datetime

from homeassistant.core import Event

from .const import (
    DOMAIN,
    MODEM_GATEWAY,
    CONF_REMOVE_INCOMING_SMS,
    EVT_SMS_RECEIVED,
    EVT_SMS_FORGET,
    SENSOR_LASTUPD,
    SMS_SENSOR_ID,
    SMS_SENSOR_NAME, EVT_SMS_DELETE
)

from homeassistant.helpers.entity import Entity

from homeassistant.components import logbook

from .exceptions import GSMGatewayException

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)




async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensors."""
    _LOGGER.debug(config_entry.data)
    async_add_entities([GsmModemSmsSensor(hass, config_entry)])


class GsmModemSmsSensor(Entity):
    """Representation of a Sensor."""
    _hass = None

    def __init__(self, hass, conf_entry):
        """Initialize the sensor."""
        self._state = None
        self._lastupdate = datetime.now()
        self._hass = hass
        self._messages = []
        if CONF_REMOVE_INCOMING_SMS in conf_entry.data:
            self._remove_inc_sms = conf_entry.data[CONF_REMOVE_INCOMING_SMS]
        else:
            self._remove_inc_sms = False
        self._processed_messages = set()
        self._duplicated_content = set()
        hass.bus.async_listen(EVT_SMS_RECEIVED,
                              self._handle_sms_received)
        hass.bus.async_listen(EVT_SMS_FORGET,
                              self._handle_sms_forget)
        hass.bus.async_listen(EVT_SMS_DELETE,
                              self._handle_sms_delete)
        _LOGGER.debug('Sms sensor up')
        # uawait self.update()

    def get_gateway(self):
        """Returns the modem gateway instance from hass scope"""
        return self._hass.data[DOMAIN][MODEM_GATEWAY]

    @property
    def name(self):
        """Return the name of the sensor."""
        return SMS_SENSOR_NAME

    @property
    def unique_id(self):
        """Return a unique ID."""
        return SMS_SENSOR_ID

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.
        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        return {SENSOR_LASTUPD: self._lastupdate.strftime('%Y-%m-%dT%H:%M:%S')}

    @property
    def should_poll(self):
        """No polling needed."""
        return True

    async def _handle_sms_received(self, call):
        await self.async_update()
        self.async_write_ha_state()

    async def _handle_sms_forget(self, call):
        self._processed_messages = set()
        self._duplicated_content = set()
        _LOGGER.debug('[_handle_sms_forget] Cleared processed_messages list')
        await self._handle_sms_received(call)

    async def _handle_sms_delete(self, call: Event):
        message_path = call.data['path']
        if message_path is None:
            raise GSMGatewayException('No message path specified')
        _LOGGER.debug('_handle_sms_delete:' + call.data['path'])
        gateway = self.get_gateway()
        await gateway.delete_sms_message(message_path)

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        gateway = self.get_gateway()
        messages = gateway.get_sms_messages()
        self._lastupdate = datetime.now()
        if messages is None:
            self._state = 'Unknown'
        else:
            self._messages = messages
            self._state = len(self._messages)
            if len(self._messages) == 0:
                return

            _LOGGER.debug('[update] CONF_REMOVE_INCOMING_SMS:' +
                          str(self._remove_inc_sms))
            _LOGGER.debug('[update] Messages count:' +
                          str(len(self._messages)))

            for message in self._messages:
                message_content = message.number + '|' + message.text + '|' + message.timestamp
                if (message.path not in self._processed_messages) and (message_content not in self._duplicated_content):
                    _LOGGER.debug(message.path)
                    self._processed_messages.add(message.path)
                    self._duplicated_content.add(message_content)

                    logbook.async_log_entry( # FIXME should be sync here?
                        self._hass,
                        SMS_SENSOR_NAME,
                        message.text,
                        DOMAIN,
                        SMS_SENSOR_ID)

                    _LOGGER.debug('[update] Firing event: ' + DOMAIN + '_incoming_sms for ' + message.path)
                    self._hass.bus.async_fire(event_type=DOMAIN + '_incoming_sms',
                                        event_data={'path': message.path,
                                               'number': message.number,
                                               'timestamp': message.timestamp,
                                               'text': message.text})
                    if self._remove_inc_sms:
                        await gateway.delete_sms_message(message.path)

                else:
                    _LOGGER.debug('[update] Skipping as already processed: ' + message.path)
                    await gateway.delete_sms_message(message.path)
