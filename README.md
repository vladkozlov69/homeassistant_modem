# ModemManager for Home Assistant

This custom integration connects Home Assistant to a cellular modem managed by
Linux ModemManager and NetworkManager. It exposes modem registration and signal
information, and provides services for SMS, dialing, and LTE connection control.

## Installation

On the `develop` branch, the integration files are in
`custom_components/mm_modem` within this repository. Install that directory as
`custom_components/mm_modem` in the Home Assistant configuration. Adding this
entire repository as a submodule at that destination nests the integration one
level too deep for Home Assistant to discover it.

The Home Assistant host must have ModemManager and NetworkManager configured for
the modem, and the Home Assistant process must have permission to access them.
See the [NetworkManager cellular connection documentation](https://docs.ubuntu.com/core/en/stacks/network/network-manager/docs/configure-cellular-connections)
for host setup details.

## Configuration

Add the integration to `configuration.yaml`; it will be imported into the
Home Assistant integration setup:

```yaml
mm_modem:
  connection_name: Unite
```

`connection_name` is the NetworkManager connection profile used when bringing
the LTE connection up or down. It can also be changed in the integration's
options.

## Entities and services

The integration creates a connectivity binary sensor with modem status,
operator, and signal strength attributes. It registers these services:

- `mm_modem.send_sms` with `phone_number` and `message` fields.
- `mm_modem.dial` with a `phone_number` field.
- `mm_modem.lte_up` and `mm_modem.lte_down` to control the configured LTE connection.

The integration requires `python-networkmanager` and a working Linux
ModemManager/NetworkManager setup.
