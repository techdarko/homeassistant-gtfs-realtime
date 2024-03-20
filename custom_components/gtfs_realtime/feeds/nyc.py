from collections.abc import Iterable
import os
import sys
import warnings

from gtfs_station_stop.station_stop_info import StationStopInfoDatabase
from gtfs_station_stop.trip_info import TripInfoDatabase
import yaml

from ..const import (
    API_KEY,
    DOMAIN,
    GTFS_STATIC_DATA,
    PLATFORM,
    ROUTE_ICONS,
    ROUTE_ID,
    STOP_ID,
    URL_ENDPOINTS,
)

STATIC_REGULAR = "http://web.mta.info/developers/data/nyct/subway/google_transit.zip"
STATIC_SUPPLEMENTAL = (
    "http://web.mta.info/developers/files/google_transit_supplemented.zip"
)

FEEDS = {
    "A": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "C": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "E": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "B": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "D": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "F": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "FX": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "M": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "J": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "Z": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "N": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "Q": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "R": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "W": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "1": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "2": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "3": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "4": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "5": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "5X": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "6": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "6X": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "7": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "7X": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "SIR": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
    "alerts": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts",
}


def subway(
    route_ids: Iterable[str],
    stop_ids: Iterable[str],
    api_key: str = "",
    route_icons: os.PathLike | None = None,
) -> str:
    print("Generating config for NYC Subway...", file=sys.stderr)
    print(f"Stops:   {[s for s in stop_ids]}", file=sys.stderr)
    print(f"Routes:  {[r for r in route_ids]}", file=sys.stderr)
    print(f"Icons:   {route_icons}", file=sys.stderr)
    print(f"API Key: {'***' if api_key else 'None'}", file=sys.stderr)

    try:
        ssi_db = StationStopInfoDatabase([STATIC_REGULAR, STATIC_SUPPLEMENTAL])
    except:  # noqa: E722
        ssi_db = StationStopInfoDatabase([])
    try:
        ti_db = TripInfoDatabase([STATIC_REGULAR, STATIC_SUPPLEMENTAL])
    except:  # noqa: E722
        ti_db = TripInfoDatabase([])

    # TODO add more robust route checker that to gtfs_station_stop library
    valid_route_ids = {ti.route_id for ti in ti_db._trip_infos.values()}
    for route_id in route_ids:
        if route_id not in valid_route_ids:
            warnings.warn("Route ID is not in the set of valid IDs", RuntimeWarning)

    gtfs_config = {
        DOMAIN: {
            API_KEY: api_key,
            URL_ENDPOINTS: [
                x
                for x in {FEEDS.get(route_id) for route_id in route_ids + ["alerts"]}
                if x is not None
            ],
            GTFS_STATIC_DATA: [STATIC_REGULAR, STATIC_SUPPLEMENTAL],
        }
    }

    if route_icons is not None:
        gtfs_config[DOMAIN][ROUTE_ICONS] = route_icons

    for stop_id in stop_ids:
        nb_stop_id = None
        sb_stop_id = None

        # Generate northbound or southbound stop_id or both if it's the parent station
        # TODO update gtfs_staiton_stop to allow selection of child stations from parents
        if stop_id[-1] == "N":
            nb_stop_id = stop_id
        elif stop_id[-1] == "S":
            sb_stop_id = stop_id
        else:
            nb_stop_id = stop_id + "N"
            sb_stop_id = stop_id + "S"

        if nb_stop_id is not None:
            stop = ssi_db._station_stop_infos.get(nb_stop_id)
            gtfs_config[
                f"sensor northbound {stop.name if stop is not None else nb_stop_id}"
            ] = [{PLATFORM: DOMAIN, STOP_ID: f"{nb_stop_id}"}]

        if sb_stop_id is not None:
            stop = ssi_db._station_stop_infos.get(sb_stop_id)
            gtfs_config[
                f"sensor southbound {stop.name if stop is not None else sb_stop_id}"
            ] = [{PLATFORM: DOMAIN, STOP_ID: f"{sb_stop_id}"}]

    for route_id in route_ids:
        gtfs_config[f"binary_sensor {route_id} alert"] = [
            {PLATFORM: DOMAIN, ROUTE_ID: route_id}
        ]

    return yaml.safe_dump(gtfs_config)
