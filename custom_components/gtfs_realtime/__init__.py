"""The GTFS Realtime integration."""
# GTFS Station Stop Feed Subject serves as the data hub for the integration

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
    DOMAIN,
    GTFS_STATIC_DATA,
    ROUTE_ICONS,
    SSI_DB,
    TI_DB,
    URL_ENDPOINTS,
)
from .coordinator import GtfsRealtimeCoordinator

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
    ssi_db = StationStopInfoDatabase(gtfs_static_zip)
    ti_db = TripInfoDatabase(gtfs_static_zip)
    cal_db = Calendar(gtfs_static_zip)
    # Attempt to perform an update to verify configuration
    hub.update()
    coordinator = GtfsRealtimeCoordinator(hass, hub)
    hass.data[DOMAIN] = {
        SSI_DB: ssi_db,
        TI_DB: ti_db,
        CAL_DB: cal_db,
        "coordinator": coordinator,
        ROUTE_ICONS: route_icons,
    }
    if ROUTE_ICONS in config[DOMAIN]:
        hass.data[DOMAIN][ROUTE_ICONS] = config[DOMAIN][ROUTE_ICONS]

    for platform in PLATFORMS:
        hass.helpers.discovery.load_platform(platform, DOMAIN, {}, config)
    return True
