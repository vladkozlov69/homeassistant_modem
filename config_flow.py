"""Config flow for SMS integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_DEVICE

from .const import DOMAIN  # pylint:disable=unused-import
from .gateway import create_modem_gateway

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required(CONF_DEVICE): str})


async def get_operator_name_from_config(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    gateway = await create_modem_gateway(hass)
    if not gateway:
        raise CannotConnect

    operator_name = await gateway.get_operator_name_async()

    # Return info that you want to store in the config entry.
    return operator_name


class SMSFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMS integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors = {}
        if user_input is not None:
            try:
                operator_name = await get_operator_name_from_config(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(operator_name)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=operator_name, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input):
        """Handle import."""
        return await self.async_step_user(user_input)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
