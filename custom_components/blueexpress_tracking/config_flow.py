"""Config flow: add one tracking number per integration entry."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .api import valid_tracking_number
from .const import CONF_LABEL, CONF_TRACKING_NUMBER, DOMAIN


class BlueExpressTrackingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Add multiple packages by adding the integration multiple times."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            number = str(user_input[CONF_TRACKING_NUMBER]).strip()
            label = str(user_input.get(CONF_LABEL, "")).strip()
            if not valid_tracking_number(number):
                errors["base"] = "invalid_tracking"
            elif len(label) > 64:
                errors["base"] = "invalid_label"
            else:
                await self.async_set_unique_id(number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=label or f"Blue Express {number}",
                    data={
                        CONF_TRACKING_NUMBER: number,
                        CONF_LABEL: label,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TRACKING_NUMBER): str,
                vol.Optional(CONF_LABEL, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
