"""The GTFS Realtime integration."""
# GTFS Station Stop Feed Subject serves as the data hub for the integration

import calendar
from pathlib import Path

from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop_info import StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfoDatabase
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    API_KEY,
    CAL_DB,
    COORDINATOR_REALTIME,
    COORDINATOR_STATIC,
    DOMAIN,
    GTFS_STATIC_DATA,
    ROUTE_ICONS,
    SSI_DB,
    TI_DB,
    URL_ENDPOINTS,
)
from .coordinator import GtfsRealtimeCoordinator, GtfsStaticCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(API_KEY): cv.string,
                vol.Required(URL_ENDPOINTS): vol.All([cv.url]),
                vol.Optional(GTFS_STATIC_DATA): vol.All([cv.url]),
                vol.Optional(ROUTE_ICONS): cv.path,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up GTFS Realtime Feed Subject for use by all sensors."""
    hub = FeedSubject(config[DOMAIN][API_KEY], config[DOMAIN][URL_ENDPOINTS])
    gtfs_static_zip = config[DOMAIN][GTFS_STATIC_DATA]
    route_icons = config[DOMAIN].get(ROUTE_ICONS)  # optional
    # Attempt to perform an update to verify configuration
    hub.update()
    coordinator_realtime = GtfsRealtimeCoordinator(hass, hub)
    coordinator_static = GtfsStaticCoordinator(hass, gtfs_static_zip)
    hass.data[DOMAIN] = {
        COORDINATOR_REALTIME: coordinator_realtime,
        COORDINATOR_STATIC: coordinator_static,
        CAL_DB: coordinator_static.calendar,
        SSI_DB: coordinator_static.station_stop_info_db,
        TI_DB: coordinator_static.trip_info_db,
        ROUTE_ICONS: route_icons,
    }
    if ROUTE_ICONS in config[DOMAIN]:
        hass.data[DOMAIN][ROUTE_ICONS] = config[DOMAIN][ROUTE_ICONS]

    for platform in PLATFORMS:
        hass.helpers.discovery.load_platform(platform, DOMAIN, {}, config)
    return True
