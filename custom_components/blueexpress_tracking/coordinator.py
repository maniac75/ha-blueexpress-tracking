"""Single-shipment, scheduled polling of the public Blue Express tracker."""

from datetime import datetime, timezone
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BlueExpressClient, BlueExpressError
from .const import DEFAULT_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BlueExpressCoordinator(DataUpdateCoordinator[dict]):
    """Refresh one shipment every 30 minutes, without retry storms."""

    def __init__(self, hass, tracking_number: str, client: BlueExpressClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{tracking_number}",
            update_interval=DEFAULT_INTERVAL,
        )
        self.tracking_number = tracking_number
        self.client = client

    async def _async_update_data(self) -> dict:
        """Preserve the last successful reading if provider becomes unavailable."""
        try:
            result = await self.client.fetch(self.tracking_number)
        except BlueExpressError as err:
            raise UpdateFailed(str(err)) from err
        result["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return result
