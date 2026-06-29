#!/usr/bin/env python3
"""CruiseFeed API — Python example: paginate and filter /cruises.

    pip install requests
    export CRUISEFEED_API_KEY=...        # Windows: set CRUISEFEED_API_KEY=...
    python python_example.py
"""

from __future__ import annotations

import os
import sys

import requests

BASE = "https://api.cruisefeed.io"


def get_cruises(**filters) -> list[dict]:
    """Yield all matching sailings, following pagination (limit/offset)."""
    key = os.environ.get("CRUISEFEED_API_KEY")
    if not key:
        sys.exit("Set CRUISEFEED_API_KEY in your environment.")
    headers = {"x-api-key": key}
    out, offset, page = [], 0, 200
    while True:
        params = {**filters, "limit": page, "offset": offset}
        r = requests.get(f"{BASE}/cruises", headers=headers, params=params, timeout=30)
        r.raise_for_status()
        body = r.json()
        items = body["items"]
        out.extend(items)
        offset += len(items)
        if len(items) < page or offset >= body.get("total", 0):
            break
    return out


if __name__ == "__main__":
    cruises = get_cruises(region="Alaska", min_nights=7, max_price=2000)
    print(f"{len(cruises)} Alaska sailings (7+ nights, <= $2000)\n")
    for c in cruises[:10]:
        ports = " > ".join(stop["port"] for stop in c.get("itinerary", []))
        print(f'{c["departure_date"]}  {c["cruise_line"]:<18} {c["title"]:<28} '
              f'${c["price_amount"]:<6} {ports}')
