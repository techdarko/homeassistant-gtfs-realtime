"""Test Coordinator."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from freezegun.api import FrozenDateTimeFactory
from gtfs_station_stop.calendar import Calendar, Service, ServiceDays
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_info import RouteInfo, RouteInfoDatabase
from gtfs_station_stop.station_stop_info import StationStopInfo, StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfo, TripInfoDatabase
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.gtfs_realtime.const import (
    CLEAR_STATIC_FEEDS,
    DOMAIN,
    REFRESH_STATIC_FEEDS,
)
from custom_components.gtfs_realtime.coordinator import GtfsRealtimeCoordinator


@pytest.fixture
async def entry_v2_and_coordinator_patch(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, entry_v2_full: MockConfigEntry
):
    """Fixture for testing using config version 2."""
    with (
        patch(
            "gtfs_station_stop.feed_subject.FeedSubject.async_update",
            new_callable=AsyncMock,
            return_value=None,
        ) as hub_update_patch,
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
        assert hub_update_patch.call_count == 0
        entry_v2_full.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry_v2_full.entry_id)
        await hass.async_block_till_done()
        assert hub_update_patch.call_count >= 1
        assert entry_v2_full.runtime_data.last_static_update
        yield entry_v2_full, hub_update_patch


def test_coordinator_construction(hass: HomeAssistant):
    """Smoke test for creating a coordinator."""
    GtfsRealtimeCoordinator(hass, feed_subject=FeedSubject([]))


async def test_update_static_data(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, entry_v2_and_coordinator_patch
):
    """Test updates through the coordinator."""
    entry_v2, coordinator_patch = entry_v2_and_coordinator_patch
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Check second call to update on gtfs1 with 2 hour refresh
    start_call_count: int = coordinator_patch.call_count
    freezer.tick(timedelta(hours=2.1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert coordinator_patch.call_count == start_call_count + 1

    # Check second call to update on gtfs2 with 10 day refresh
    # Find a way to track each source independently
    start_call_count: int = coordinator_patch.call_count
    freezer.tick(timedelta(days=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert coordinator_patch.call_count == start_call_count + 1

    sensor_state = hass.states.get("sensor.1_101n")
    assert sensor_state.state == STATE_UNKNOWN


async def test_clear_static_data_service(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, entry_v2_and_coordinator_patch
):
    """Test clearing static data."""
    entry_v2, _ = entry_v2_and_coordinator_patch
    coordinator: GtfsRealtimeCoordinator = entry_v2.runtime_data
    coordinator.calendar.services["Normal"] = Service(
        "X",
        ServiceDays.no_service(),
        start=date(year=2024, month=12, day=1),
        end=date(year=2024, month=12, day=31),
    )
    coordinator.station_stop_info_db.station_stop_infos["Stop"] = StationStopInfo(
        {"stop_id": "Stop"}
    )
    coordinator.route_info_db.route_infos["Route"] = RouteInfo(
        {
            "route_id": "Route",
            "route_long_name": "Long Route Name",
            "route_type": "1",
        }
    )
    coordinator.trip_info_db.trip_infos["Trip"] = TripInfo(
        {"trip_id": "Trip", "route_id": "Route", "service_id": "Normal"}
    )
    await hass.services.async_call(DOMAIN, CLEAR_STATIC_FEEDS, blocking=True)
    await hass.async_block_till_done()
    assert len(coordinator.calendar.services) == 0
    assert len(coordinator.station_stop_info_db.station_stop_infos) == 0
    assert len(coordinator.route_info_db.route_infos) == 0
    assert len(coordinator.trip_info_db.trip_infos) == 0


@pytest.mark.skip("May require debouncing")
async def test_refresh_static_data_service(
    hass: HomeAssistant, entry_v2_and_coordinator_patch
):
    """Test refreshing static data."""
    _, coordinator_patch = entry_v2_and_coordinator_patch
    before_call_count = coordinator_patch.call_count
    await hass.services.async_call(DOMAIN, REFRESH_STATIC_FEEDS, blocking=True)
    await hass.async_block_till_done()
    assert coordinator_patch.call_count == before_call_count + 1
