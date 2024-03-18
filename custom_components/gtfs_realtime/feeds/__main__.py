#!/usr/bin/python
import argparse

from .nyc import subway

parser = argparse.ArgumentParser(prog="GTFS Feed Bootstrapper", description="Module for bootstrapping config files with the necessary setup.")
parser.add_argument('gtfs_feed')
parser.add_argument(
    "-s",
    "--stops",
    help="list of stops to check for arrivals and alerts",
    nargs="*",
    default=[],
)
parser.add_argument(
    "-r", "--routes", help="list of routes to check for alerts", nargs="*", default=[]
)
parser.add_argument(
    "-k", "--api-key", help="API key from GTFS provider", default=""
)
parser.add_argument("-i", "--route-icons", help="directory of route icons", default=None)

args = parser.parse_args()

if args.gtfs_feed == 'nyc.subway':
    print(subway(args.routes, args.stops, args.api_key, args.route_icons))
