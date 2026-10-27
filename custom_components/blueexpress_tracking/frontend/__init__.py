"""Optional Lovelace card resource packaged with the Blue Express integration.

Registered once per Home Assistant startup; no dashboard cards are created.
"""

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA, MODE_STORAGE
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
CARD_PATH = Path(__file__).parent / "blueexpress-tracking-card.js"
CARD_URL = "/blueexpress_tracking/blueexpress-tracking-card.js"
CARD_VERSION = "0.2.0"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve bundled JS and register Lovelace resource if in storage mode."""
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(CARD_PATH), False)]
        )
        lovelace = hass.data.get(LOVELACE_DATA)
        if not lovelace or lovelace.resource_mode != MODE_STORAGE:
            _LOGGER.info(
                "Blue Express card available at %s; add module resource manually "
                "if using Lovelace YAML resource mode",
                CARD_URL,
            )
            return
        resources = lovelace.resources
        if not resources.loaded:
            await resources.async_load()

        versioned = f"{CARD_URL}?v={CARD_VERSION}"
        matches = [
            item for item in resources.async_items()
            if item.get("url", "").split("?")[0] == CARD_URL
        ]
        if matches:
            current = matches[0]
            if current.get("url") != versioned or current.get("type", current.get("res_type")) != "module":
                await resources.async_update_item(
                    current["id"], {"url": versioned, "res_type": "module"}
                )
        else:
            await resources.async_create_item(
                {"url": versioned, "res_type": "module"}
            )
    except Exception:
        # Card failures must never prevent delivery sensors from working.
        _LOGGER.exception(
            "Unable to register optional Blue Express card. "
            "Manually add %s as a JavaScript module in dashboard resources.",
            CARD_URL,
        )
