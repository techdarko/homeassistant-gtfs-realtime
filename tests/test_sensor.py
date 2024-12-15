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
def arrival_sensor(hass: HomeAssistant) -> ArrivalSensor:
    """Fixture for a basic arrival sensor."""
    feed_subject = FeedSubject([])
    station_stop = StationStop("STATION", feed_subject)
    station_stop.arrivals = [
        Arrival((NOW + timedelta(minutes=24)).timestamp(), "A", "A_trip"),
        Arrival((NOW + timedelta(minutes=36)).timestamp(), "B", "B_trip"),
    ]

    async def noop():
        pass

    arrival_sensor = ArrivalSensor(
        GtfsRealtimeCoordinator(hass, feed_subject), station_stop, 0
    )
    arrival_sensor.async_write_ha_state = noop
    return arrival_sensor


def test_create_entity(arrival_sensor):
    """Tests entity construction."""
    # Created by the fixture
    assert arrival_sensor.state is None
    assert arrival_sensor.name == "1: STATION"


@freeze_time(NOW)
def test_update(arrival_sensor):
    """
    Tests calling the update method on the sensor.

    This will latch the data in station_stop into the hass platform.
    """
    arrival_sensor.update()
    assert arrival_sensor.state == pytest.approx(24)


@freeze_time(NOW)
def test_update_trip_info_not_found(arrival_sensor):
    """Tests that missing trip info still updates the state."""
    arrival_sensor.trip_info_db = TripInfoDatabase()
    arrival_sensor.update()
