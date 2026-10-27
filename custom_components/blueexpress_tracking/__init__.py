"""Unofficial Blue Express shipment tracking for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BlueExpressClient
from .const import CONF_TRACKING_NUMBER
from .coordinator import BlueExpressCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure one tracked shipment from the user-created entry."""
    client = BlueExpressClient(async_get_clientsession(hass))
    coordinator = BlueExpressCoordinator(hass, entry.data[CONF_TRACKING_NUMBER], client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop polling and unload the shipment without touching other integrations."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
