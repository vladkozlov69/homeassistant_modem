
import unittest
from unittest.mock import Mock, call

from homeassistant.core import EventBus

from custom_components.mm_modem.gateway import Gateway
from custom_components.mm_modem.sensor import GsmModemSmsSensor
from custom_components.mm_modem.sms_message import SmsMessage

class GsmModemSmsSensorTest(unittest.TestCase):
    def test_init(self):
        mock_gateway = Mock(spec=Gateway)
        mock_gateway.get_sms_messages.return_value = []
        sensor = GsmModemSmsSensor(Mock(bus=Mock(), data={'mm_modem': {'MM_MODEM_GATEWAY': mock_gateway}}), Mock(data={}))
        assert sensor.name == 'GSM Modem SMS'
        assert sensor.state == 0

    def test_update_new_messages(self):
        mock_gateway = Mock(spec=Gateway)
        mock_bus = Mock(spec=EventBus)
        mock_gateway.get_sms_messages.return_value = [
            SmsMessage(path='/m/p/1', number='01234', text='msg text', timestamp='dd-mm-2025'),
            SmsMessage(path='/m/p/2', number='01234', text='msg text2', timestamp='dd-mm-2025'),
        ]
        sensor = GsmModemSmsSensor(Mock(bus=mock_bus, data={'mm_modem': {'MM_MODEM_GATEWAY': mock_gateway}}), Mock(data={}))
        assert sensor.state == 2

        calls = [
            call(event_type='mm_modem_incoming_sms',
                 event_data={'path': '/m/p/1', 'number': '01234', 'timestamp': 'dd-mm-2025', 'text': 'msg text'}),
            call(event_type='mm_modem_incoming_sms',
                 event_data={'path': '/m/p/2', 'number': '01234', 'timestamp': 'dd-mm-2025', 'text': 'msg text2'})
        ]
        mock_bus.fire.assert_has_calls(calls)
        assert mock_bus.fire.call_count == 2


    def test_update_new_messages_skip_existing(self):
        mock_gateway = Mock(spec=Gateway)
        mock_bus = Mock(spec=EventBus)
        mock_gateway.get_sms_messages.return_value = [
            SmsMessage(path='/m/p/1', number='01234', text='msg text', timestamp='dd-mm-2025'),
            SmsMessage(path='/m/p/2', number='01234', text='msg text2', timestamp='dd-mm-2025'),
        ]
        sensor = GsmModemSmsSensor(Mock(bus=mock_bus, data={'mm_modem': {'MM_MODEM_GATEWAY': mock_gateway}}), Mock(data={}))
        assert sensor.state == 2
        mock_gateway.get_sms_messages.return_value = [
            SmsMessage(path='/m/p/1', number='01234', text='msg text', timestamp='dd-mm-2025'),
            SmsMessage(path='/m/p/3', number='01234', text='msg text2', timestamp='dd-mm-2025'),
        ]
        sensor.update()
        assert sensor.state == 2

        calls = [
            call(event_type='mm_modem_incoming_sms',
                 event_data={'path': '/m/p/1', 'number': '01234', 'timestamp': 'dd-mm-2025', 'text': 'msg text'}),
            call(event_type='mm_modem_incoming_sms',
                 event_data={'path': '/m/p/2', 'number': '01234', 'timestamp': 'dd-mm-2025', 'text': 'msg text2'}),
            call(event_type='mm_modem_incoming_sms',
                 event_data={'path': '/m/p/3', 'number': '01234', 'timestamp': 'dd-mm-2025', 'text': 'msg text2'})
        ]
        mock_bus.fire.assert_has_calls(calls)
        assert mock_bus.fire.call_count == 3

if __name__ == '__main__':
    unittest.main()