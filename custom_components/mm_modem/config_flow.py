import logging
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from .const import DOMAIN, CONF_CONNECTION_NAME

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONNECTION_NAME): str
    }
)

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)

type ConfigType = Mapping[str, Any] | None

class MDMConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """MDMLink config flow."""

    def __init__(self) -> None:
        """Init config flow."""
        self._errors = {}

    async def async_step_import(
        self, platform_config: ConfigType
    ) -> config_entries.ConfigFlowResult:
        _LOG.info("platform_config")
        _LOG.info(platform_config)
        return self.async_create_entry(title="configuration.yaml", data=platform_config)


    async def async_step_user(self, user_input: ConfigType = None) -> config_entries.ConfigFlowResult:
        """Import a config entry."""
        user_input = {}
        return self.async_create_entry(title="MDMLink Config", data={})
#        pass
        #return self.async_abort(reason="DDD")
