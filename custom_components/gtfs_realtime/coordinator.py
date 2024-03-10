"""GTFS Realtime Coordinator."""
import asyncio
from collections.abc import Iterable
from datetime import timedelta
import logging
import os

from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop_info import StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfoDatabase
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class GtfsRealtimeCoordinator(DataUpdateCoordinator):
    """GTFS Realtime Update Coordinator."""

    def __init__(self, hass: HomeAssistant, feed_subject: FeedSubject) -> None:
        """Initialize the GTFS Update Coordinator to notify all entities upon poll."""
        super().__init__(
            hass, _LOGGER, name="GTFS Realtime", update_interval=timedelta(seconds=60)
        )
        self.hub = feed_subject

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with asyncio.timeout(10):
            self.hub.update()

class GtfsStaticCoordinator(DataUpdateCoordinator):
    """GTFS Static Update Coordinator. Polls Static Data Endpoints for new data on a slower basis."""

    def __init__(self, hass: HomeAssistant, gtfs_static_zip: Iterable[os.PathLike] | os.PathLike | None = None) -> None:
        """Initialize the GTFS Update Coordinator to notify all entities upon poll."""
        super().__init__(
            hass, _LOGGER, name="GTFS Static", update_interval=timedelta(days=1)
        )
        # Save the resource path to reload periodically
        self.gtfs_static_zip = gtfs_static_zip
        self.calendar = Calendar(gtfs_static_zip)
        self.station_stop_info_db = StationStopInfoDatabase(gtfs_static_zip)
        self.trip_info_db = TripInfoDatabase(gtfs_static_zip)

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with asyncio.timeout(10):
            self.calendar.services.clear()
            self.calendar.add_gtfs_data(self.gtfs_static_zip)

            self.station_stop_info_db._station_stop_infos.clear()
            self.station_stop_info_db.add_gtfs_data(self.gtfs_static_zip)

            self.trip_info_db._trip_infos.clear()
            self.trip_info_db.add_gtfs_data(self.gtfs_static_zip)
