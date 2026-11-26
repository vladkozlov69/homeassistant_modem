# ModemManager for Home Assistant

This custom integration connects Home Assistant to a cellular modem managed by
Linux ModemManager and NetworkManager. It exposes modem registration and signal
information, and provides services for SMS, dialing, and LTE connection control.

## Installation

The integration files are at the root of this repository. Add this repository
as a submodule at `custom_components/mm_modem` in a Home Assistant configuration
repository, or copy the repository contents to that directory:

```sh
git submodule add -b develop git@github.com:vladkozlov69/homeassistant_modem.git custom_components/mm_modem
```

The Home Assistant host must have ModemManager and NetworkManager configured for
the modem, and the Home Assistant process must have permission to access them.
See the [NetworkManager cellular connection documentation](https://docs.ubuntu.com/core/en/stacks/network/network-manager/docs/configure-cellular-connections)
for host setup details.

## Configuration

Configure the integration in `configuration.yaml`:

```yaml
mm_modem:
  connection_name: Unite
  remove_incoming_sms: false
```

`connection_name` selects the NetworkManager profile used by the LTE services.
`remove_incoming_sms` controls whether incoming messages are removed after
processing.

## Entities and services

The integration creates a connectivity binary sensor with modem status,
operator, and signal strength attributes. It registers these services:

- `mm_modem.send_sms` with `number` and `message` fields.
- `mm_modem.delete_sms` with an `sms_path` field.
- `mm_modem.dial` with a `number` field.
- `mm_modem.lte_up`, `mm_modem.lte_down`, and `mm_modem.sms_forget`.

The integration requires Linux ModemManager and NetworkManager, including the
GObject introspection bindings listed in `requirements.txt`. The Home Assistant
process must be able to access the system D-Bus and manage the modem.
