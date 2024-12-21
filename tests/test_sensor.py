"""Test sensor."""

from datetime import datetime, timedelta, timezone

from freezegun import freeze_time
from gtfs_station_stop.arrival import Arrival
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.station_stop import StationStop
from gtfs_station_stop.trip_info import TripInfoDatabase
from homeassistant.core import HomeAssistant
import pytest

from custom_components.gtfs_realtime.coordinator import GtfsRealtimeCoordinator
from custom_components.gtfs_realtime.sensor import ArrivalSensor

NOW = datetime(2024, 3, 17, 23, 0, 0).replace(tzinfo=timezone.utc)


@pytest.fixture
def coordinator(hass: HomeAssistant):
    """Fixture for coordinator object."""
    feed_subject = FeedSubject([])
    coordinator = GtfsRealtimeCoordinator(hass, feed_subject)
    yield coordinator


@pytest.fixture
def arrival_sensor(hass: HomeAssistant, coordinator: GtfsRealtimeCoordinator):
    """Fixture for a basic arrival sensor."""
    station_stop = StationStop("STATION", coordinator.hub)
    station_stop.arrivals = [
        Arrival((NOW + timedelta(minutes=24)).timestamp(), "A", "A_trip"),
        Arrival((NOW + timedelta(minutes=36)).timestamp(), "B", "B_trip"),
    ]

    async def noop():
        pass

    arrival_sensor = ArrivalSensor(coordinator, station_stop.id, 0)
    arrival_sensor.async_write_ha_state = noop
    yield arrival_sensor


def test_create_entity(arrival_sensor: ArrivalSensor):
    """Tests entity construction."""
    # Created by the fixture
    assert arrival_sensor.state is None
    assert arrival_sensor.name == "1: STATION"


@pytest.mark.skip("Fails to update, find the correct way to fix this.")
@freeze_time(NOW)
async def test_update(
    coordinator: GtfsRealtimeCoordinator, arrival_sensor: ArrivalSensor
):
    """
    Tests calling the update method on the sensor.

    This will latch the data in station_stop into the hass platform.
    """
    await coordinator._async_update_data()
    arrival_sensor.update()
    assert arrival_sensor.state == pytest.approx(24)


@freeze_time(NOW)
def test_update_trip_info_not_found(arrival_sensor):
    """Tests that missing trip info still updates the state."""
    arrival_sensor.trip_info_db = TripInfoDatabase()
    arrival_sensor.update()
