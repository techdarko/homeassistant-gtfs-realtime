"""Platform for sensor integration."""
from __future__ import annotations

import os
from pathlib import Path

from gtfs_station_stop.arrival import Arrival
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

from .const import ARRIVAL_LIMIT, DOMAIN, ROUTE_ICONS, STOP_ID
from .coordinator import GtfsRealtimeCoordinator

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend({
    vol.Required(STOP_ID): cv.string,
    vol.Optional(ARRIVAL_LIMIT, default=4): int
    })


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    coordinator: GtfsRealtimeCoordinator = hass.data[DOMAIN]["coordinator"]
    if discovery_info is None:
        if STOP_ID in config:
            ssi_db: StationStopInfoDatabase = hass.data[DOMAIN]["ssi_db"]
            ti_db: TripInfoDatabase = hass.data[DOMAIN]["ti_db"]
            station_stop = StationStop(config[STOP_ID], coordinator.hub)
            arrival_limit: int = config.get(ARRIVAL_LIMIT, 4)
            route_icons: os.PathLike = hass.data[DOMAIN].get(ROUTE_ICONS)
            add_entities(
                [
                    ArrivalSensor(
                        coordinator,
                        station_stop,
                        ssi_db[station_stop.id],
                        ti_db,
                        i,
                        route_icons=route_icons,
                    )
                    for i in range(arrival_limit)
                ]
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
        station_stop_info: StationStopInfo | None,
        trip_info_db: TripInfoDatabase | None,
        idx: int,
        route_icons: os.PathLike | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.station_stop = station_stop
        self.station_stop_info = station_stop_info
        self.trip_info_db = trip_info_db
        self._idx = idx
        self.route_icons = route_icons
        self._name = self._get_station_ref()
        self._attr_unique_id = f"arrival_{self.station_stop.id}_{self._idx}"
        self._attr_suggested_display_precision = 0
        self._attr_suggested_unit_of_measurement = UnitOfTime.MINUTES

    def _get_station_ref(self):
        return (
            self.station_stop_info.name
            if self.station_stop_info is not None
            else self.station_stop.stop_id
        )

    @property
    def name(self) -> str:
        """Name of the station from static data or else the Stop ID."""
        return self._name

    @callback
    def _handle_coordinator_update(self) -> None:
        time_to_arrivals = sorted(self.station_stop.get_time_to_arrivals())
        self._name = self._get_station_ref()
        if len(time_to_arrivals) > self._idx:
            time_to_arrival: Arrival = time_to_arrivals[self._idx]
            self._attr_native_value = max(time_to_arrival.time, 0) # do not allow negative numbers
            self._name = f"{time_to_arrival.route} {self._name}"
            if self.route_icons is not None:
                self._attr_entity_picture = str(
                    Path(self.route_icons) / (time_to_arrival.route + ".svg")
                )
            if self.trip_info_db is not None:
                trip_info = self.trip_info_db.get_close_match(time_to_arrival.trip)
                if trip_info is not None:
                    self._name = f"{self._name} to {trip_info.trip_headsign}"
        else:
            self._attr_native_value = None
        self.async_write_ha_state()
