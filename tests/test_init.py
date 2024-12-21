"""Test component setup."""

from datetime import timedelta
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gtfs_realtime.const import (
    CONF_API_KEY,
    CONF_GTFS_STATIC_DATA,
    CONF_ROUTE_ICONS,
    CONF_STATIC_SOURCES_UPDATE_FREQUENCY,
    CONF_STATIC_SOURCES_UPDATE_FREQUENCY_DEFAULT,
    CONF_URL_ENDPOINTS,
    DOMAIN,
)


async def test_async_setup(hass: HomeAssistant) -> None:
    """Test the component gets setup."""
    test_config = {
        DOMAIN: {
            CONF_API_KEY: "",
            CONF_URL_ENDPOINTS: [],
            CONF_GTFS_STATIC_DATA: [],
            CONF_ROUTE_ICONS: "",
        }
    }
    assert await async_setup_component(hass, DOMAIN, test_config) is True


async def test_migrate_from_v1(
    hass: HomeAssistant,
    entry_v1_full: MockConfigEntry,
) -> None:
    """Test Migration From Version 1."""

    with patch(
        "gtfs_station_stop.feed_subject.FeedSubject.async_update", return_value=None
    ), patch(
        "custom_components.gtfs_realtime.coordinator.GtfsRealtimeCoordinator.async_update_static_data",
        return_value=None,
    ):
        entry_v1_full.add_to_hass(hass)

        await hass.config_entries.async_setup(entry_v1_full.entry_id)

    await hass.async_block_till_done()

    # Adds default time for each static data url
    updated_entry = hass.config_entries.async_get_entry(entry_v1_full.entry_id)

    static_data_uris = [
        "http://example.com/gtfs1.zip",
        "http://example.com/gtfs2.zip",
    ]
    assert set(static_data_uris) == set(updated_entry.data.get(CONF_GTFS_STATIC_DATA))

    for uri in static_data_uris:
        # update everything to the default
        timedelta_dict = updated_entry.data.get(
            CONF_STATIC_SOURCES_UPDATE_FREQUENCY
        ).get(uri)
        assert (
            timedelta_dict.get("hours") == CONF_STATIC_SOURCES_UPDATE_FREQUENCY_DEFAULT
        )
        assert timedelta(**timedelta_dict) == timedelta(
            hours=CONF_STATIC_SOURCES_UPDATE_FREQUENCY_DEFAULT
        )
