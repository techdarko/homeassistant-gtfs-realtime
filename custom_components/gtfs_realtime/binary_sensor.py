"""Platform for binary sensor integration."""
from __future__ import annotations

from gtfs_station_stop.route_status import RouteStatus
from gtfs_station_stop.station_stop import StationStop
from gtfs_station_stop.station_stop_info import StationStopInfo, StationStopInfoDatabase
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
    ALERT_LIMIT,
    COORDINATOR_REALTIME,
    COORDINATOR_STATIC,
    DESCRIPTION_PRETTY,
    DOMAIN,
    HEADER_PRETTY,
    ROUTE_ID,
    SSI_DB,
    STOP_ID,
)
from .coordinator import GtfsRealtimeCoordinator, GtfsStaticCoordinator

PLATFORM_SCHEMA = BINARY_SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(
            vol.Any(ROUTE_ID, STOP_ID),
            msg=f"Must specify at least one of ['{ROUTE_ID}', 'f{STOP_ID}']",
        ): cv.string,
        vol.Optional(ALERT_LIMIT, default=4): int
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    alert_limit: int = config.get(ALERT_LIMIT, 4)
    coordinator: GtfsRealtimeCoordinator = hass.data[DOMAIN][COORDINATOR_REALTIME]
    if discovery_info is None:
        if STOP_ID in config:
            ssi_db: StationStopInfoDatabase = hass.data[DOMAIN][SSI_DB]
            station_stop = StationStop(config[STOP_ID], coordinator.hub)
            add_entities(
                [
                    AlertSensor(
                        coordinator,
                        station_stop,
                        ssi_db[station_stop.id],
                        i,
                        hass.config.language,
                    )
                    for i in range(alert_limit)
                ]
            )
        elif ROUTE_ID in config:
            route_status = RouteStatus(config[ROUTE_ID], coordinator.hub)
            add_entities(
                [
                    AlertSensor(
                        coordinator,
                        route_status,
                        i,
                        hass.config.language,
                        None
                    )
                    for i in range(alert_limit)
                ]
            )


class AlertSensor(BinarySensorEntity, CoordinatorEntity):
    """Representation of a Station GTFS Realtime Alert Sensor."""

    CLEAN_ALERT_DATA = {HEADER_PRETTY: "", DESCRIPTION_PRETTY: ""}

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: GtfsRealtimeCoordinator,
        informed_entity: StationStop | RouteStatus,
        idx: int,
        language: str = "",
        station_stop_info: StationStopInfo | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.informed_entity = informed_entity
        self.language = language
        self._name: str = f"{station_stop_info.name if station_stop_info is not None else informed_entity.id} Service Alerts"
        self._attr_is_on = False
        self._idx = idx
        self._alert_detail: dict[str, str] = AlertSensor.CLEAN_ALERT_DATA
        self._attr_unique_id = f"alert_{informed_entity.id}_{self._idx}"

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
        if len(alerts) == 0:
            self._attr_is_on = False
        elif len(alerts) > self._idx:
            self._attr_is_on = True
            self._alert_detail[HEADER_PRETTY] = alerts[self._idx].header_text.get(
                self.language, ""
            )
            self._alert_detail[DESCRIPTION_PRETTY] = alerts[self._idx].description_text.get(
                self.language, ""
            )
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update()
