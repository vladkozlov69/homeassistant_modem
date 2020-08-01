
import logging

import voluptuous as vol

from homeassistant import config_entries
from .const import DOMAIN, ATTR_CONNECTION_NAME

from homeassistant.core import callback

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONNECTION_NAME): str
    }
)

_LOGGER = logging.getLogger(__name__)


class MMLteConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Returns flow handler"""
        return MMLteConfigOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            print("=> one_instance_allowed")
            return self.async_abort(reason="one_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(title="MM Lte Config1", data=user_input)


class MMLteConfigOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle SpeedTest options."""
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        print(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="MM Lte Config2", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        ATTR_CONNECTION_NAME,
                        default=self.config_entry.options.get(
                            ATTR_CONNECTION_NAME
                        ),
                    ): str
                }
            ),
        )
