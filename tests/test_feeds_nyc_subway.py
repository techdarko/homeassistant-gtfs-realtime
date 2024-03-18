"""Tests for NYC Subway feed setup."""

from custom_components.gtfs_realtime.feeds.nyc import subway


def test_create_config_for_nyc_subway_feed():
    """Tests that the subway function can be used without Error."""
    subway(["1"], ["101N"])
    # generates some output on std::out, no assert
