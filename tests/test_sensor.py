"""Test sensor."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from freezegun.api import FrozenDateTimeFactory
from gtfs_station_stop.arrival import Arrival
from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.route_info import RouteInfoDatabase
from gtfs_station_stop.station_stop_info import StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfoDatabase
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.gtfs_realtime.coordinator import GtfsRealtimeCoordinator


async def test_smoke(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, entry_v2_nodialout
):
    """Smoke test the sensor platform."""
    with (
        patch(
            "gtfs_station_stop.feed_subject.FeedSubject.async_update",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "custom_components.gtfs_realtime.coordinator.GtfsRealtimeCoordinator._async_update_static_data",
            new_callable=AsyncMock,
            return_value=(
                Calendar(),
                StationStopInfoDatabase(),
                TripInfoDatabase(),
                RouteInfoDatabase(),
            ),
        ),
    ):
        entry_v2_nodialout.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry_v2_nodialout.entry_id)
        await hass.async_block_till_done()

    coordinator: GtfsRealtimeCoordinator = entry_v2_nodialout.runtime_data
    coordinator.route_icons = None
    coordinator.hub.realtime_feed_uris = []

    async def coordinator_update_side_effects():
        for x in range(4):
            arrivals = {
                "101N": [
                    Arrival(datetime.now() + timedelta(minutes=4 - x), "A", ""),
                    Arrival(datetime.now() + timedelta(minutes=6 - x), "B", ""),
                    Arrival(datetime.now() + timedelta(minutes=8 - x), "C", ""),
                ],
                "102S": [
                    Arrival(datetime.now() + timedelta(minutes=9 - x), "X", ""),
                    Arrival(datetime.now() + timedelta(minutes=13 - x), "Y", ""),
                    Arrival(datetime.now() + timedelta(minutes=17 - x), "Z", ""),
                ],
            }
            for id, stop in coordinator.station_stops.items():
                stop.arrivals = next(arrivals)[id]
                yield
        pytest.fail("Tests should not call the update more than 4 times")

    coordinator.hub.async_update = AsyncMock()
    coordinator.hub.async_update.side_effect = coordinator_update_side_effects

    freezer.tick(timedelta(minutes=1.1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    # Need to figure out how to mock setting the state
    # assert hass.states.get("sensor.1_101n").state == 4
    # assert hass.states.get("sensor.2_101n").state == 6
    # assert hass.states.get("sensor.3_101n").state == 8
    assert hass.states.get("sensor.4_101n").state == STATE_UNKNOWN
    # assert hass.states.get("sensor.1_102s").state == 9
    # assert hass.states.get("sensor.2_102s").state == 13
    # assert hass.states.get("sensor.3_102s").state == 17
    assert hass.states.get("sensor.4_102s").state == STATE_UNKNOWN
    freezer.tick(timedelta(minutes=1.1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    # assert hass.states.get("sensor.1_101n").state == 3
    # assert hass.states.get("sensor.2_101n").state == 5
    # assert hass.states.get("sensor.3_101n").state == 7
    assert hass.states.get("sensor.4_101n").state == STATE_UNKNOWN
    # assert hass.states.get("sensor.1_102s").state == 8
    # assert hass.states.get("sensor.2_102s").state == 12
    # assert hass.states.get("sensor.3_102s").state == 16
    assert hass.states.get("sensor.4_102s").state == STATE_UNKNOWN
