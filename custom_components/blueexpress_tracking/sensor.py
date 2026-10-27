"""Status and non-sensitive shipment history in one Home Assistant sensor."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LABEL, CONF_TRACKING_NUMBER, DOMAIN
from .coordinator import BlueExpressCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one tracking sensor for this config entry."""
    async_add_entities([BlueExpressShipmentSensor(entry, entry.runtime_data)])


class BlueExpressShipmentSensor(CoordinatorEntity[BlueExpressCoordinator], SensorEntity):
    """One shipment with an update timestamp, ETA and filtered event history."""

    _attr_has_entity_name = True
    _attr_translation_key = "status"
    _attr_icon = "mdi:truck-delivery"

    def __init__(self, entry, coordinator: BlueExpressCoordinator) -> None:
        super().__init__(coordinator)
        self._number = entry.data[CONF_TRACKING_NUMBER]
        self._attr_unique_id = f"{DOMAIN}_{self._number}_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._number)},
            name=entry.data.get(CONF_LABEL) or f"Blue Express {self._number}",
            manufacturer="Blue Express (fuente pública no oficial)",
            model="Seguimiento de envío",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Keep last valid value visible, marked stale when offline."""
        return self.coordinator.data is not None

    @property
    def native_value(self) -> str | None:
        """Return the published delivery stage, not a guessed translation."""
        return self.coordinator.data.get("status") if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict:
        """Expose only public delivery fields and clearly mark stale readings."""
        data = self.coordinator.data or {}
        return {
            "tracking_number": self._number,
            "carrier": "Blue Express",
            "promise_date": data.get("promise_date"),
            "last_movement": data.get("last_movement"),
            "event_count": data.get("event_count"),
            "events": data.get("events", []),
            "source_url": data.get("source_url"),
            "fetched_at": data.get("fetched_at"),
            "stale": not self.coordinator.last_update_success,
        }
