"""Constants for modem Component."""

DOMAIN = 'mm_modem'
MODEM_GATEWAY = 'MM_MODEM_GATEWAY'

ATTR_PHONE_NUMBER = 'number'
ATTR_MESSAGE = 'message'
ATTR_CONNECTION_NAME = 'connection_name'
ATTR_SMS_PATH = 'sms_path'

CONF_CONNECTION_NAME = 'connection_name'
CONF_REMOVE_INCOMING_SMS = 'remove_incoming_sms'

EVT_MODEM_CONNECTED = DOMAIN + '_modem_connected'
EVT_MODEM_DISCONNECTED = DOMAIN + '_modem_disconnected'
EVT_SMS_RECEIVED = DOMAIN + '_sms_received'
