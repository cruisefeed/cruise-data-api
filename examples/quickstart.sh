#!/usr/bin/env bash
# CruiseFeed API quickstart (curl). Requires: export CRUISEFEED_API_KEY=...
# Every endpoint requires the key (sent as the x-api-key header).
set -euo pipefail

BASE="https://api.cruisefeed.io"
KEY="${CRUISEFEED_API_KEY:-}"
auth=(-H "x-api-key: ${KEY}")

echo "# Reference lists (key required)"
curl -s "${auth[@]}" "$BASE/cruise-lines" | head -c 200; echo
curl -s "${auth[@]}" "$BASE/ports"        | head -c 200; echo

echo; echo "# List & filter cruises"
curl -s "${auth[@]}" "$BASE/cruises?region=Caribbean&max_price=1200&min_nights=5&limit=3"

echo; echo "# One sailing by natural key (source/source_id)"
curl -s "${auth[@]}" "$BASE/cruises/cruisemapper/msc-world-europa-2026-09-12"

echo; echo "# Price history for that sailing"
curl -s "${auth[@]}" "$BASE/cruises/cruisemapper/msc-world-europa-2026-09-12/history"

echo; echo "# Recent price changes (fare-drop alerts)"
curl -s "${auth[@]}" "$BASE/changes?since=2026-06-20&cruise_line=MSC%20Cruises&limit=5"

echo; echo "# CSV export -> cruises.csv"
curl -s "${auth[@]}" "$BASE/cruises.csv?region=Caribbean&max_price=1200" -o cruises.csv
echo "wrote cruises.csv"
