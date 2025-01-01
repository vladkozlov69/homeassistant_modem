import unittest
from unittest.mock import Mock

from gateway import Gateway
from sensor import GsmModemSmsSensor

class GsmModemSmsSensorTest(unittest.TestCase):
    def test_name(self):
        mockGateway = Mock(spec=Gateway)
        mockGateway.get_sms_messages.return_value = []
        sensor = GsmModemSmsSensor(Mock(bus=Mock(), data={'mm_modem': {'MM_MODEM_GATEWAY': mockGateway}}), Mock(data={}))
        assert sensor.name == 'GSM Modem SMS'


if __name__ == '__main__':
    unittest.main()