"""Test component setup."""

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.gtfs_realtime.const import (
    CONF_API_KEY,
    CONF_GTFS_STATIC_DATA,
    CONF_URL_ENDPOINTS,
    DOMAIN,
)


async def test_async_setup(hass: HomeAssistant) -> None:
    """Test the component gets setup."""
    test_config = {
        DOMAIN: {CONF_API_KEY: "", CONF_URL_ENDPOINTS: [], CONF_GTFS_STATIC_DATA: []}
    }
    assert await async_setup_component(hass, DOMAIN, test_config) is True
