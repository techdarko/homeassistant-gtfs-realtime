"""Test component setup."""

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.gtfs_realtime.const import DOMAIN, URL_ENDPOINTS


async def test_async_setup(hass: HomeAssistant) -> None:
    """Test the component gets setup."""
    test_config = {DOMAIN: {URL_ENDPOINTS: []}}
    assert await async_setup_component(hass, DOMAIN, test_config) is True
