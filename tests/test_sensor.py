"""Test sensor."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from freezegun.api import FrozenDateTimeFactory
from gtfs_station_stop.arrival import Arrival
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from syrupy.assertion import SnapshotAssertion

from custom_components.gtfs_realtime.coordinator import (
    GtfsRealtimeCoordinator,
    GtfsUpdateData,
)


async def test_setup_sensors(hass: HomeAssistant, entry_v2_nodialout: MockConfigEntry):
    """Test setting ups sensors in integration."""
    with (
        patch(
            "custom_components.gtfs_realtime.coordinator.GtfsRealtimeCoordinator._async_update_data",  # noqa E501
            new_callable=AsyncMock,
        ),
        patch(
            "custom_components.gtfs_realtime.coordinator.GtfsRealtimeCoordinator.async_update_static_data",  # noqa E501
            new_callable=AsyncMock,
        ),
    ):
        entry_v2_nodialout.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry_v2_nodialout.entry_id)
        await hass.async_block_till_done()
        assert hass.states.get("sensor.4_101n").state == STATE_UNKNOWN


async def test_update(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    entry_v2_nodialout: MockConfigEntry,
    snapshot: SnapshotAssertion,
):
    """Smoke test the sensor platform."""
    start_time = datetime.now()
    with (
        patch(
            "custom_components.gtfs_realtime.coordinator.FeedSubject.async_update",  # noqa E501
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "custom_components.gtfs_realtime.coordinator.GtfsRealtimeCoordinator.async_update_static_data",  # noqa E501
            new_callable=AsyncMock,
            return_value=GtfsUpdateData(),
        ),
    ):
        entry_v2_nodialout.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry_v2_nodialout.entry_id)
        await hass.async_block_till_done()

    coordinator: GtfsRealtimeCoordinator = entry_v2_nodialout.runtime_data
    coordinator.route_icons = None
    coordinator.hub.realtime_feed_uris = []

    @dataclass
    class UpdateCounter:
        update_count: int = 0

    update_counter = UpdateCounter(update_count=0)

    def make_ts(minutes) -> float:
        return (
            start_time + timedelta(minutes=minutes - update_counter.update_count)
        ).timestamp()

    def coordinator_update_side_effects():
        arrivals = {
            "101N": [
                Arrival(make_ts(4), "A", ""),
                Arrival(make_ts(6), "B", ""),
                Arrival(make_ts(8), "C", ""),
            ],
            "102S": [
                Arrival(make_ts(9), "X", ""),
                Arrival(make_ts(13), "Y", ""),
                Arrival(make_ts(17), "Z", ""),
            ],
        }
        for id, stop in coordinator.gtfs_update_data.station_stops.items():
            stop.arrivals = arrivals[id]
        update_counter.update_count += 1
        return

    coordinator.hub.async_update = AsyncMock()
    coordinator.hub.async_update.side_effect = coordinator_update_side_effects
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert coordinator.hub.async_update.call_count == 1

    for sensor in [
        "1_101n",
        "2_101n",
        "3_101n",
        "4_101n",
        "1_102s",
        "2_102s",
        "3_102s",
        "4_102s",
    ]:
        assert (
            snapshot(name=f"{sensor}-after-1-minute")
            == hass.states.get(f"{SENSOR_DOMAIN}.{sensor}").state
        )
