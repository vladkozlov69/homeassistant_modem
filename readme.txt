Add this to configuration.yaml:

mm_modem:


binary_sensor:
  - platform: mm_modem
    unique_id: "sensor.mm_modem"

sensor:
  - platform: template
    sensors:
      mm_modem_info:
        friendly_name: "GSM Modem Info"
        entity_id:
          - binary_sensor.gsm_modem
        value_template: "{{ state_attr('binary_sensor.gsm_modem', 'cell_operator') }}/{{ state_attr('binary_sensor.gsm_modem', 'modem_status') }}, {{ state_attr('binary_sensor.gsm_modem', 'signal_strength') }} dB"
