"""GTFS Realtime Coordinator."""
import asyncio
from datetime import timedelta
import logging

from gtfs_station_stop.feed_subject import FeedSubject
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
