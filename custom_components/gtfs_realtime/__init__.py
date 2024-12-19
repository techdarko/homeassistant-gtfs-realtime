"""The GTFS Realtime integration."""

# GTFS Station Stop Feed Subject serves as the data hub for the integration

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_info import RouteInfoDatabase
from gtfs_station_stop.station_stop_info import StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfoDatabase
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import voluptuous as vol

from custom_components.gtfs_realtime.config_flow import DOMAIN_SCHEMA

from .const import (
    CONF_API_KEY,
    CONF_GTFS_STATIC_DATA,
    CONF_ROUTE_ICONS,
    CONF_STATIC_SOURCES_UPDATE_FREQUENCY,
    CONF_STATIC_SOURCES_UPDATE_FREQUENCY_DEFAULT,
    CONF_URL_ENDPOINTS,
    DOMAIN,
)
from .coordinator import GtfsRealtimeCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: DOMAIN_SCHEMA},
    extra=vol.ALLOW_EXTRA,
)


@dataclass
class GtfsProviderData:
    """Class for maintaining data received from a GTFS provider."""

    coordinator: GtfsRealtimeCoordinator
    calendar: Calendar
    ssi_db: StationStopInfoDatabase
    ti_db: TripInfoDatabase
    rti_db: RouteInfoDatabase
    rt_icons: str | None


type GtfsRealtimeConfigEntry = ConfigEntry[GtfsRealtimeCoordinator]

_LOGGER = logging.getLogger(__name__)


async def _async_create_gtfs_update_hub(hass: HomeAssistant, config: dict[str, Any]):
    hub = FeedSubject(
        config[CONF_URL_ENDPOINTS], headers={"api_key": config[CONF_API_KEY]}
    )
    route_icons: str | None = config.get(CONF_ROUTE_ICONS)  # optional
    # Attempt to perform an update to verify configuration
    await hub.async_update()

    static_timedelta = {
        uri: timedelta(**timedelta_dict)
        for uri, timedelta_dict in config[CONF_STATIC_SOURCES_UPDATE_FREQUENCY].items()
    }
    # if the value is 0, it is likely user input errors due to a bug in config flow UI, so coerce it to the default
    for value in static_timedelta.values():
        if value == timedelta(seconds=0):
            value = timedelta(hours=CONF_STATIC_SOURCES_UPDATE_FREQUENCY_DEFAULT)
    coordinator = GtfsRealtimeCoordinator(
        hass,
        hub,
        config[CONF_GTFS_STATIC_DATA],
        static_timedelta=static_timedelta,
    )
    # Update the static data for the coordinator before the first update
    await coordinator.async_update_static_data(config[CONF_GTFS_STATIC_DATA])

    gtfs_provider_data = GtfsProviderData(
        coordinator,
        coordinator.calendar,
        coordinator.station_stop_info_db,
        coordinator.trip_info_db,
        coordinator.route_info_db,
        route_icons,
    )

    hass.data.setdefault(DOMAIN, {})[coordinator.get_lookup_id()] = gtfs_provider_data
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: GtfsRealtimeConfigEntry
) -> bool:
    """Set up GTFS Realtime Feed Subject for use by all sensors."""
    await _async_create_gtfs_update_hub(hass, entry.data)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: GtfsRealtimeConfigEntry
) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )
    if config_entry.version > 1:
        return False
    if config_entry.version == 1:
        new_data = {**config_entry.data}
        new_data[CONF_STATIC_SOURCES_UPDATE_FREQUENCY] = {}
        for uri in new_data[CONF_GTFS_STATIC_DATA]:
            _LOGGER.debug(
                f"Static data source {uri} set to update on interval of {timedelta(seconds=CONF_STATIC_SOURCES_UPDATE_FREQUENCY_DEFAULT)}"
            )
            new_data[CONF_STATIC_SOURCES_UPDATE_FREQUENCY][uri] = {
                "hours": CONF_STATIC_SOURCES_UPDATE_FREQUENCY_DEFAULT
            }
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=2, minor_version=0
        )
    return True
