"""Test Config Flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gtfs_realtime.config_flow import GtfsRealtimeConfigFlow
from custom_components.gtfs_realtime.const import CONF_GTFS_STATIC_DATA, DOMAIN


@pytest.fixture
def flow():
    """Fixture that constructs the flow."""

    # feeds call is now no-op
    def no_feeds():
        return {}

    GtfsRealtimeConfigFlow._get_feeds = no_feeds
    return GtfsRealtimeConfigFlow()


async def test_form(hass: HomeAssistant, flow) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM


async def test_step_user(flow) -> None:
    """Test User Setup through Config Flow."""
    await flow.async_step_user(None)


async def test_user_step_get_feeds_fails(flow) -> None:
    """Test that failures getting feeds do not break config flow."""

    def fail():
        raise RuntimeError("This must fail.")

    GtfsRealtimeConfigFlow._get_feeds = fail
    flow_result = await flow.async_step_user(None)
    assert "base" in flow_result["errors"]


async def test_step_choose_static_and_realtime_feeds(flow) -> None:
    """Test config flow for choosing static and realtime feeds."""
    await flow.async_step_choose_static_and_realtime_feeds({})


async def test_step_choose_informed_entities(flow) -> None:
    """Test config flow for choosing informed entities."""
    await flow.async_step_choose_informed_entities(
        user_input={CONF_GTFS_STATIC_DATA: []}
    )


@pytest.mark.skip(reason="Need to Reimplement Reconfiguration Step")
async def test_step_reconfigure(hass: HomeAssistant, entry_v1: MockConfigEntry) -> None:
    """Test Reconfigure."""
    entry_v1.add_to_hass(hass)
    old_entry_data = entry_v1.data.copy()
    result = await entry_v1.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"gtfs_static_data_update_frequency_hours": 15}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    entry = hass.config_entries.async_get_entry(entry_v1.entry_id)
    assert entry.data == {**old_entry_data, **entry.data}
    assert entry.data["gtfs_static_data_update_frequency_hours"] == 15
