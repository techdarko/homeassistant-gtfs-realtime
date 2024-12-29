"""Fixtures for testing."""

from datetime import date
import json
from pathlib import Path

from gtfs_station_stop.calendar import Service, ServiceDays
from gtfs_station_stop.route_info import RouteInfo
from gtfs_station_stop.schedule import GtfsSchedule
from gtfs_station_stop.station_stop_info import StationStopInfo
from gtfs_station_stop.trip_info import TripInfo
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.extensions.amber import AmberSnapshotExtension
from syrupy.location import PyTestLocation

from custom_components.gtfs_realtime.config_flow import DOMAIN

DIFFERENT_DIRECTORY = "snapshots"


class DifferentDirectoryExtension(AmberSnapshotExtension):
    @classmethod
    def dirname(cls, *, test_location: "PyTestLocation") -> str:
        return str(Path(test_location.filepath).parent.joinpath(DIFFERENT_DIRECTORY))


@pytest.fixture
def snapshot(snapshot):
    return snapshot.use_extension(DifferentDirectoryExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integration that will be tested."""
    yield


@pytest.fixture(name="entry_v1")
def create_config_entry_v1():
    """Fixture for entry version 1."""
    yield MockConfigEntry(
        entry_id="mock_config_v1",
        domain=DOMAIN,
        version=1,
        minor_version=0,
        data={"url_endpoints": ["https://gtfs.example.com/feed"]},
    )


@pytest.fixture(name="entry_v1_full")
def create_config_entry_v1_full():
    """Fixture with full mock data for entry version 1."""
    with open("tests/fixtures/config_entry_v1_full.json") as f:
        conf = json.load(f)
    yield MockConfigEntry(**conf)


@pytest.fixture(name="entry_v2_full")
def create_config_entry_v2_full():
    """Fixture with full mock data for entry version 2."""
    with open("tests/fixtures/config_entry_v2_full.json") as f:
        conf = json.load(f)
    yield MockConfigEntry(**conf)


@pytest.fixture(name="entry_v2_nodialout")
def create_config_entry_v2_nodialout():
    """Fixture with mock data for entry version 2 with limited URLs to access."""
    with open("tests/fixtures/config_entry_v2_nodialout.json") as f:
        conf = json.load(f)
    yield MockConfigEntry(**conf)


@pytest.fixture
def mock_schedule():
    mock_schedule = GtfsSchedule()
    mock_schedule.calendar.services["Normal"] = Service(
        "X",
        ServiceDays.no_service(),
        start=date(year=2024, month=12, day=1),
        end=date(year=2024, month=12, day=31),
    )
    mock_schedule.station_stop_info_ds.station_stop_infos["Stop"] = StationStopInfo(
        {"stop_id": "Stop"}
    )
    mock_schedule.route_info_ds.route_infos["Route"] = RouteInfo(
        {
            "route_id": "Route",
            "route_long_name": "Long Route Name",
            "route_type": "1",
        }
    )
    mock_schedule.trip_info_ds.trip_infos["Trip"] = TripInfo(
        {"trip_id": "Trip", "route_id": "Route", "service_id": "Normal"}
    )
    return mock_schedule
