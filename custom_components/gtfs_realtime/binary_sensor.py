"""Platform for binary sensor integration."""

from __future__ import annotations

from gtfs_station_stop.route_status import RouteStatus
from gtfs_station_stop.station_stop import StationStop
from gtfs_station_stop.station_stop_info import StationStopInfo
from homeassistant.components.binary_sensor import (
    PLATFORM_SCHEMA as BINARY_SENSOR_PLATFORM_SCHEMA,
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import voluptuous as vol

from .const import (
    CONF_GTFS_STATIC_DATA,
    CONF_ROUTE_IDS,
    CONF_URL_ENDPOINTS,
    DOMAIN,
    ROUTE_ID,
    STOP_ID,
)
from .coordinator import GtfsRealtimeCoordinator

PLATFORM_SCHEMA = BINARY_SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(
            vol.Any(ROUTE_ID, STOP_ID),
            msg=f"Must specify at least one of ['{ROUTE_ID}', 'f{STOP_ID}']",
        ): cv.string
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    lookup_id = GtfsRealtimeCoordinator.make_lookup_id(
        realtime_feed_urls=config.data[CONF_URL_ENDPOINTS],
        gtfs_static_zip=config.data[CONF_GTFS_STATIC_DATA],
    )
    coordinator: GtfsRealtimeCoordinator = hass.data[DOMAIN][lookup_id].coordinator
    if discovery_info is None:
        if CONF_ROUTE_IDS in config.data:
            add_entities(
                [
                    AlertSensor(
                        coordinator,
                        RouteStatus(route_id, coordinator.hub),
                        hass.config.language,
                        None,
                    )
                    for route_id in config.data[CONF_ROUTE_IDS]
                ]
            )


class AlertSensor(BinarySensorEntity, CoordinatorEntity):
    """Representation of a Station GTFS Realtime Alert Sensor."""

    CLEAN_ALERT_DATA = {"header_0": "", "description_0": ""}

    _attr_translation_key = "alert_descriptions"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: GtfsRealtimeCoordinator,
        informed_entity: StationStop | RouteStatus,
        language: str = "",
        station_stop_info: StationStopInfo | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.informed_entity = informed_entity
        self.language = language
        self._name: str = f"{station_stop_info.name if station_stop_info is not None else informed_entity.id} Service Alerts"
        self._attr_is_on = False
        self._alert_detail: dict[str, str] = AlertSensor.CLEAN_ALERT_DATA
        self._attr_unique_id = f"alert_{informed_entity.id}"

    @property
    def name(self) -> str | None:
        """Name of the Sensor."""
        return self._name

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Explanation of Alerts for a given Stop ID."""
        return self._alert_detail

    def update(self) -> None:
        alerts = self.informed_entity.alerts
        self._alert_detail = {}
        if len(alerts) == 0:
            self._attr_is_on = False
        elif len(alerts) > 0:
            self._attr_is_on = True
            for i, alert in enumerate(alerts):
                self._alert_detail[f"header_{i}"] = alert.header_text.get(
                    self.language, ""
                )
                self._alert_detail[f"description_{i}"] = alert.description_text.get(
                    self.language, ""
                )
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update()
