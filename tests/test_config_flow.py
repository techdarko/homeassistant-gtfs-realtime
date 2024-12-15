"""Test Config Flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import RESULT_TYPE_FORM
import pytest

from custom_components.gtfs_realtime.config_flow import GtfsRealtimeConfigFlow
from custom_components.gtfs_realtime.const import CONF_GTFS_STATIC_DATA, DOMAIN


@pytest.fixture
def flow():
    """Fixture that constructs the flow."""

    # feeds call is now no-op
    def no_feeds():
        return {}

    GtfsRealtimeConfigFlow.get_feeds = no_feeds
    return GtfsRealtimeConfigFlow()


@pytest.mark.skip("Fixture might be failing this.")
async def test_form(hass: HomeAssistant, flow):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] is None


async def test_step_user(flow):
    """Test User Setup through Config Flow."""
    await flow.async_step_user(None)


async def test_user_step_get_feeds_fails(flow):
    """Test that failures getting feeds do not break config flow."""

    def fail():
        raise RuntimeError("This must fail.")

    GtfsRealtimeConfigFlow.get_feeds = fail
    flow_result = await flow.async_step_user(None)
    assert "base" in flow_result["errors"]


async def test_step_choose_static_and_realtime_feeds(flow):
    """Test config flow for choosing static and realtime feeds."""
    await flow.async_step_choose_static_and_realtime_feeds({})


async def test_step_choose_informed_entities(flow):
    """Test config flow for choosing informed entities."""
    await flow.async_step_choose_informed_entities(
        user_input={CONF_GTFS_STATIC_DATA: []}
    )
