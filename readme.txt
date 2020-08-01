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






Add to /etc/polkit-1/localauthority/50-local.d/allow-ssh-networking.pkla

[Let adm group modify system settings for network]
Identity=unix-group:*
Action=org.freedesktop.NetworkManager.network-control
ResultAny=yes




Add to /etc/polkit-1/localauthority/50-local.d/ModemManager.pkla

[ModemManager]
Identity=unix-user:*
Action=org.freedesktop.ModemManager1.*
ResultAny=yes
ResultActive=yes
ResultInactive=yes


https://docs.ubuntu.com/core/en/stacks/network/network-manager/docs/configure-cellular-connections

///https://www.ricmedia.com/set-permanent-dns-nameservers-ubuntu-debian-resolv-conf/