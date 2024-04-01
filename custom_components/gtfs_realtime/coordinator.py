"""GTFS Realtime Coordinator."""

import asyncio
from collections.abc import Iterable
from datetime import timedelta
import logging
import os

from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_info import RouteInfoDatabase
from gtfs_station_stop.static_database import async_factory
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
        await self.hub.async_update()


class GtfsStaticCoordinator(DataUpdateCoordinator):
    """GTFS Static Update Coordinator. Polls Static Data Endpoints for new data on a slower basis."""

    def __init__(
        self,
        hass: HomeAssistant,
        gtfs_static_zip: Iterable[os.PathLike] | os.PathLike | None = None,
        **kwargs,
    ) -> None:
        """Initialize the GTFS Update Coordinator to notify all entities upon poll."""
        super().__init__(
            hass, _LOGGER, name="GTFS Static", update_interval=timedelta(days=1)
        )
        # Save the resource path to reload periodically
        self.gtfs_static_zip = gtfs_static_zip
        # Requests are cached, so simply await these in sequence
        self.calendar = None
        self.station_stop_info_db = None
        self.trip_info_db = None
        self.route_into_db = None
        self.kwargs = kwargs

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        async with asyncio.TaskGroup() as tg:
            cal_db_task = tg.create_task(
                async_factory(Calendar, *self.gtfs_static_zip, **self.kwargs)
            )
            ssi_db_task = tg.create_task(
                async_factory(
                    StationStopInfoDatabase, *self.gtfs_static_zip, **self.kwargs
                )
            )
            ti_db_task = tg.create_task(
                async_factory(TripInfoDatabase, *self.gtfs_static_zip, **self.kwargs)
            )
            rti_db_task = tg.create_task(
                async_factory(RouteInfoDatabase, *self.gtfs_static_zip, **self.kwargs)
            )
        (
            self.calendar,
            self.station_stop_info_db,
            self.trip_info_db,
            self.route_into_db,
        ) = (
            cal_db_task.result(),
            ssi_db_task.result(),
            ti_db_task.result(),
            rti_db_task.result(),
        )
