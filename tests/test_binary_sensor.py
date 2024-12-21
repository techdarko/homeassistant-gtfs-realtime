"""Test sensor."""

import datetime

from gtfs_station_stop.alert import Alert
from gtfs_station_stop.feed_subject import FeedSubject
from gtfs_station_stop.route_status import RouteStatus
from homeassistant.core import HomeAssistant
import pytest

from custom_components.gtfs_realtime.binary_sensor import AlertSensor
from custom_components.gtfs_realtime.coordinator import GtfsRealtimeCoordinator


@pytest.fixture
def alert_sensor(hass: HomeAssistant) -> AlertSensor:
    """Fixture for a basic alert sensor."""
    feed_subject = FeedSubject([])
    route_status = RouteStatus("1", feed_subject)
    route_status.alerts = [
        Alert(datetime.datetime.max, {"en": "Alert"}, {"en": "This is an Alert"}),
        Alert(
            datetime.datetime.max,
            {"en": "Another Alert"},
            {"en": "This is another Alert"},
        ),
    ]

    async def noop():
        pass

    alert_sensor = AlertSensor(
        GtfsRealtimeCoordinator(hass, feed_subject), route_status, "en"
    )
    alert_sensor.async_write_ha_state = noop
    return alert_sensor


def test_create_entity(alert_sensor):
    """Tests entity construction."""
    # Created by the fixture
    assert alert_sensor.state == "off"
    assert "1" in alert_sensor.name


def test_update(alert_sensor):
    """
    Tests calling the update method on the sensor.

    This will latch the data in station_stop into the hass platform.
    """
    alert_sensor.update()
    assert alert_sensor.state == "on"
    assert alert_sensor.extra_state_attributes["header_1"] == "Alert"
    assert alert_sensor.extra_state_attributes["header_2"] == "Another Alert"
    assert alert_sensor.extra_state_attributes["description_1"] == "This is an Alert"
    assert (
        alert_sensor.extra_state_attributes["description_2"] == "This is another Alert"
    )
