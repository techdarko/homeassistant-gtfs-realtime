"""Platform for sensor integration."""

from __future__ import annotations

import os
from pathlib import Path

from gtfs_station_stop.arrival import Arrival
from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.station_stop import StationStop
from gtfs_station_stop.station_stop_info import StationStopInfo, StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfoDatabase
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import voluptuous as vol

from .const import (
    ARRIVAL_LIMIT,
    CAL_DB,
    COORDINATOR_REALTIME,
    DOMAIN,
    HEADSIGN_PRETTY,
    ROUTE_ICONS,
    ROUTE_ID,
    SSI_DB,
    STOP_ID,
    TI_DB,
    TRIP_ID_PRETTY,
)
from .coordinator import GtfsRealtimeCoordinator

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {vol.Required(STOP_ID): cv.string, vol.Optional(ARRIVAL_LIMIT, default=4): int}
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    coordinator: GtfsRealtimeCoordinator = hass.data[DOMAIN][COORDINATOR_REALTIME]
    if discovery_info is None:
        if STOP_ID in config:
            ssi_db: StationStopInfoDatabase = hass.data[DOMAIN][SSI_DB]
            ti_db: TripInfoDatabase = hass.data[DOMAIN][TI_DB]
            cal_db: Calendar = hass.data[DOMAIN][CAL_DB]
            station_stop = StationStop(config[STOP_ID], coordinator.hub)
            arrival_limit: int = config.get(ARRIVAL_LIMIT, 4)
            route_icons: os.PathLike = hass.data[DOMAIN].get(ROUTE_ICONS)
            add_entities(
                [
                    ArrivalSensor(
                        coordinator,
                        station_stop,
                        i,
                        ssi_db[station_stop.id],
                        ti_db,
                        cal_db,
                        route_icons=route_icons,
                    )
                    for i in range(arrival_limit)
                ],
                update_before_add=True,
            )


class ArrivalSensor(SensorEntity, CoordinatorEntity):
    """Representation of a Station GTFS Realtime Arrival Sensor."""

    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.MINUTES
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_picture: str | None = None

    def __init__(
        self,
        coordinator: GtfsRealtimeCoordinator,
        station_stop: StationStop,
        idx: int,
        station_stop_info: StationStopInfo | None = None,
        trip_info_db: TripInfoDatabase | None = None,
        calendar_db: Calendar | None = None,
        route_icons: os.PathLike | None = None,
    ) -> None:
        """Initialize the sensor."""
        # Required
        super().__init__(coordinator)
        self.station_stop = station_stop
        self._idx = idx
        # Allowed to be `None`
        self.station_stop_info = station_stop_info
        self.trip_info_db = trip_info_db
        self.calendar_db = calendar_db
        self.route_icons = route_icons

        self._name = f"{self._idx + 1}: {self._get_station_ref()}"
        self._attr_unique_id = f"arrival_{self.station_stop.id}_{self._idx}"
        self._attr_suggested_display_precision = 0
        self._attr_suggested_unit_of_measurement = UnitOfTime.MINUTES
        self._arrival_detail: dict[str, str] = {}

    def _get_station_ref(self):
        return (
            self.station_stop_info.name
            if self.station_stop_info is not None
            else self.station_stop.id
        )

    @property
    def name(self) -> str:
        """Name of the station from static data or else the Stop ID."""
        return self._name

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Explanation of Alerts for a given Stop ID."""
        return self._arrival_detail

    @property
    def entity_picture(self) -> str | None:
        return (
            str(Path(self.route_icons) / (self._arrival_detail[ROUTE_ID] + ".svg"))
            if self.route_icons is not None
            and self._arrival_detail.get(ROUTE_ID) is not None
            else None
        )

    @property
    def icon(self) -> str:
        return "mdi:bus-clock"

    def update(self) -> None:
        time_to_arrivals = sorted(self.station_stop.get_time_to_arrivals())
        if len(time_to_arrivals) > self._idx:
            time_to_arrival: Arrival = time_to_arrivals[self._idx]
            self._attr_native_value = max(
                time_to_arrival.time, 0
            )  # do not allow negative numbers
            self._arrival_detail[ROUTE_ID] = time_to_arrival.route
            if self.trip_info_db is not None:
                trip_info = self.trip_info_db.get_close_match(
                    time_to_arrival.trip, self.calendar_db
                )
                if trip_info is not None:
                    self._arrival_detail[HEADSIGN_PRETTY] = trip_info.trip_headsign
                    self._arrival_detail[TRIP_ID_PRETTY] = trip_info.trip_id
        else:
            self._attr_native_value = None
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.update()
