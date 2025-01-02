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
EVT_LTE_CONNECTED = DOMAIN + '_lte_connected'
EVT_LTE_DISCONNECTED = DOMAIN + '_lte_disconnected'
EVT_SMS_RECEIVED = DOMAIN + '_sms_received'
EVT_SMS_FORGET = DOMAIN + '_sms_forget'
EVT_SMS_DELETE = DOMAIN + '_sms_delete'

SMS_SENSOR_ID = 'mm_modem.incoming_sms'
SMS_SENSOR_NAME = 'GSM Modem SMS'

SENSOR_LASTUPD = 'modem_lastupdate'
