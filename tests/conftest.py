"""Fixtures for testing."""

import json

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gtfs_realtime.config_flow import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integration that will be tested."""
    yield


@pytest.fixture(name="entry_v1")
def create_config_entry_v1() -> MockConfigEntry:
    """Fixture for entry version 1."""
    return MockConfigEntry(
        entry_id="mock_config_v1",
        domain=DOMAIN,
        version=1,
        minor_version=0,
        data={"url_endpoints": ["https://gtfs.example.com/feed"]},
    )


@pytest.fixture(name="entry_v1_full")
def create_config_entry_v1_full() -> MockConfigEntry:
    """Fixture with full mock data for entry version 1."""
    with open("tests/fixtures/config_entry_v1_full.json") as f:
        conf = json.load(f)
    return MockConfigEntry(**conf)
