"""Test sensor."""

from unittest.mock import AsyncMock, patch

from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.route_info import RouteInfoDatabase
from gtfs_station_stop.station_stop_info import StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfoDatabase
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_binary_sensors(
    hass: HomeAssistant, entry_v2_nodialout: MockConfigEntry
):
    """Test setting up binary sensors for integration."""
    with (
        patch(
            "custom_components.gtfs_realtime.coordinator.GtfsRealtimeCoordinator._async_update_data",
            new_callable=AsyncMock,
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
        assert hass.states.get("binary_sensor.1_service_alerts").state == STATE_OFF
        assert hass.states.get("binary_sensor.2_service_alerts").state == STATE_OFF
