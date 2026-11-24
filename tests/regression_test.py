# Copyright (c) 2026 Vladimir Kozlov <vkozloff@gmail.com>
# SPDX-License-Identifier: MIT

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from homeassistant.const import CONF_NAME

from mm_modem.binary_sensor import GsmModemSensor, LteConnectionSensor
from mm_modem.const import (
    CONF_CONNECTION_NAME,
    CONF_REMOVE_INCOMING_SMS,
    DOMAIN,
    EVT_SMS_FORGET,
    MODEM_GATEWAY,
)
from mm_modem.gateway import Gateway
from mm_modem.sensor import GsmModemSmsSensor
from mm_modem.sms_message import SmsMessage


class GatewayFixesTest(unittest.TestCase):
    def test_get_config_value_from_mapping(self):
        gateway = Gateway({CONF_NAME: "Modem", CONF_CONNECTION_NAME: "Unite"}, None)
        self.assertEqual(gateway._get_config_value(CONF_NAME), "Modem")
        self.assertEqual(gateway._get_config_value(CONF_CONNECTION_NAME), "Unite")
        self.assertIsNone(gateway._get_config_value("missing"))

    def test_get_config_value_from_config_entry_like(self):
        config_entry = SimpleNamespace(data={CONF_NAME: "Modem"}, options={CONF_CONNECTION_NAME: "LTE"})
        gateway = Gateway(config_entry, None)
        self.assertEqual(gateway._get_config_value(CONF_NAME), "Modem")
        self.assertEqual(gateway._get_config_value(CONF_CONNECTION_NAME), "LTE")

    def test_get_lte_state_matches_active_connection_name(self):
        import gi.repository.NM as NM

        gateway = Gateway({CONF_CONNECTION_NAME: "Unite"}, None)
        active = Mock()
        active.get_id.return_value = "Unite"
        client = Mock()
        client.get_active_connections.return_value = [active]
        NM.Client.new = Mock(return_value=client)

        self.assertTrue(gateway.get_lte_state())
        NM.Client.new.assert_called_once_with(None)

    def test_get_lte_state_false_when_not_active(self):
        import gi.repository.NM as NM

        gateway = Gateway({CONF_CONNECTION_NAME: "Unite"}, None)
        active = Mock()
        active.get_id.return_value = "Other"
        client = Mock()
        client.get_active_connections.return_value = [active]
        NM.Client.new = Mock(return_value=client)

        self.assertFalse(gateway.get_lte_state())


class SmsSensorFixesTest(unittest.IsolatedAsyncioTestCase):
    async def test_update_missing_gateway_is_safe(self):
        hass = Mock(data={DOMAIN: {}})
        hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *a: func(*a))
        bus = Mock()
        bus.async_listen = Mock(return_value=Mock())
        bus.async_fire = Mock()
        hass.bus = bus
        sensor = GsmModemSmsSensor(hass, Mock(data={}))

        await sensor.async_update()

        self.assertEqual(sensor.state, "Unknown")

    async def test_update_none_messages_is_safe(self):
        mock_gateway = Mock()
        mock_gateway.get_sms_messages.return_value = None
        hass = Mock(data={DOMAIN: {MODEM_GATEWAY: mock_gateway}})
        hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *a: func(*a))
        bus = Mock()
        bus.async_listen = Mock(return_value=Mock())
        bus.async_fire = Mock()
        hass.bus = bus
        sensor = GsmModemSmsSensor(hass, Mock(data={}))

        await sensor.async_update()

        self.assertEqual(sensor._messages, [])
        self.assertEqual(sensor.state, "Unknown")
        bus.async_fire.assert_not_called()

    async def test_remove_incoming_sms_deletes_new_message(self):
        mock_gateway = Mock()
        mock_gateway.get_sms_messages.return_value = [
            SmsMessage(path="/m/p/1", number="01234", text="msg", timestamp="t1"),
        ]
        mock_gateway.delete_sms_message = AsyncMock()
        hass = Mock(data={DOMAIN: {MODEM_GATEWAY: mock_gateway}})
        hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *a: func(*a))
        bus = Mock()
        bus.async_listen = Mock(return_value=Mock())
        bus.async_fire = Mock()
        hass.bus = bus
        sensor = GsmModemSmsSensor(hass, Mock(data={CONF_REMOVE_INCOMING_SMS: True}))

        await sensor.async_update()

        bus.async_fire.assert_any_call(
            event_type="mm_modem_incoming_sms",
            event_data={
                "path": "/m/p/1",
                "number": "01234",
                "timestamp": "t1",
                "text": "msg",
            },
        )
        mock_gateway.delete_sms_message.assert_awaited_once_with("/m/p/1")


class BinarySensorFixesTest(unittest.TestCase):
    def test_gsm_modem_update_missing_gateway_sets_unavailable(self):
        hass = Mock(data={DOMAIN: {}})
        bus = Mock()
        bus.async_listen = Mock(return_value=Mock())
        hass.bus = bus
        sensor = GsmModemSensor(hass)

        sensor.update()

        self.assertFalse(sensor.is_on)
        self.assertEqual(sensor.extra_state_attributes["modem_status"], "none")
        self.assertEqual(sensor.extra_state_attributes["cell_operator"], "none")
        self.assertEqual(sensor.extra_state_attributes["signal_strength"], 0)

    def test_lte_update_missing_gateway_sets_unavailable(self):
        hass = Mock(data={DOMAIN: {}})
        bus = Mock()
        bus.async_listen = Mock(return_value=Mock())
        hass.bus = bus
        sensor = LteConnectionSensor(hass)

        sensor.update()

        self.assertFalse(sensor.is_on)
        self.assertFalse(sensor._lte_status)
        self.assertEqual(sensor._modem_status, "none")


class SmsForgetEventTest(unittest.IsolatedAsyncioTestCase):
    async def test_sms_forget_fires_correct_event(self):
        from mm_modem.__init__ import async_setup_modem

        hass = Mock()
        hass.data = {DOMAIN: {}}
        hass.bus = Mock()
        hass.bus.async_listen = Mock(return_value=Mock())
        hass.bus.async_listen_once = Mock(return_value=Mock())
        hass.bus.async_fire_internal = Mock()
        hass.services = Mock()
        hass.services.has_service = Mock(return_value=False)
        hass.services.async_register = Mock()
        hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *a: func(*a))

        gateway = Mock()
        gateway.async_added_to_hass = AsyncMock()

        with patch("mm_modem.gateway.create_modem_gateway", return_value=gateway):
            await async_setup_modem(hass, {CONF_NAME: "GSM Modem"})

        calls = [c for c in hass.services.async_register.call_args_list if c.args[1] == "sms_forget"]
        self.assertTrue(calls, "sms_forget service should be registered")
        handler = calls[0].args[2]
        handler(Mock())
        hass.bus.async_fire_internal.assert_called_with(EVT_SMS_FORGET)
        self.assertEqual(EVT_SMS_FORGET, "mm_modem_sms_forget")


if __name__ == "__main__":
    unittest.main()
