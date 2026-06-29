# CruiseFeed API — Cruise Inventory & Pricing Data (REST, JSON & CSV)

**CruiseFeed is a cruise data API**: cruise lines, ships, sailing dates, day-by-day
itineraries, ports of call and lead-in pricing — normalized into one clean schema and
delivered as a JSON/CSV REST API, refreshed up to daily.

It's built for **travel agencies, OTAs, cruise-comparison sites and data aggregators**
who would rather consume one normalized cruise feed than build and maintain dozens of
scrapers. Every record carries a stable natural key (`source` + `source_id`) and the
same shape across every cruise line.

- 🌐 Website & pricing: **https://cruisefeed.io**
- 📦 Free sample of your target lines/region: **support@cruisefeed.io**
- 📑 Machine-readable schema: [`openapi.yaml`](openapi.yaml) · 💻 Examples: [`examples/`](examples/)

```bash
# every sailing in the Caribbean under $1,200, as JSON
curl -H "x-api-key: $CRUISEFEED_API_KEY" \
  "https://api.cruisefeed.io/cruises?region=Caribbean&max_price=1200&limit=5"
```

---

## What's in the feed

| | |
|---|---|
| **Cruise lines & ships** | 100+ lines (Royal Caribbean, MSC, Carnival, Norwegian, Princess, Celebrity, Viking, Disney, AIDA …) with normalized names |
| **Sailings** | departure & return dates across the booking window, by ship and region |
| **Itineraries** | day-by-day ports of call with country, plus embark/disembark ports |
| **Pricing** | lead-in fare + price-per-night, with daily price/availability **history** for change tracking |
| **Delivery** | REST JSON, CSV export, or push to your S3 / warehouse · refreshed monthly → daily by plan |

One normalized schema across all lines, deduplicated, with stable IDs. The data is
public cruise inventory only — no personal data.

## Authentication

All `/cruises*`, `/changes` and history endpoints require an API key, sent as the
`x-api-key` header. The reference lists (`/cruise-lines`, `/ships`, `/ports`) are public.

```bash
curl -H "x-api-key: YOUR_API_KEY" "https://api.cruisefeed.io/cruises?limit=1"
```

Get a key at **https://cruisefeed.io**.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/cruises` | ✅ | List & filter sailings (the workhorse) |
| GET | `/cruises.csv` | ✅ | Same filters, streamed as CSV |
| GET | `/cruises/{source}/{source_id}` | ✅ | Get one sailing by natural key |
| GET | `/cruises/{source}/{source_id}/history` | ✅ | Price & availability history |
| GET | `/changes` | ✅ | Recent price changes (fare-drop alerts) |
| GET | `/cruise-lines` | — | Distinct cruise line names |
| GET | `/ships` | — | Distinct ship names |
| GET | `/ports` | — | Distinct departure ports |

Full request/response details are in [`openapi.yaml`](openapi.yaml) — paste it into
[Swagger Editor](https://editor.swagger.io) or Postman to explore.

### Filters for `GET /cruises`

`source` · `cruise_line` · `ship_name` · `embark_port` · `region` (partial) ·
`departure_from` · `departure_to` · `min_price` · `max_price` · `min_nights` ·
`max_nights` · `round_trip` · `dedupe` (default true) · `sort` (default
`departure_date`) · `limit` (1–200, default 50) · `offset`.

## Example: list cruises

**Request**

```bash
curl -H "x-api-key: $CRUISEFEED_API_KEY" \
  "https://api.cruisefeed.io/cruises?cruise_line=MSC%20Cruises&max_price=1500&min_nights=5&limit=1"
```

**Response**

```json
{
  "items": [
    {
      "source": "cruisemapper",
      "source_id": "msc-world-europa-2026-09-12",
      "cruise_line": "MSC Cruises",
      "ship_name": "MSC World Europa",
      "title": "7-Night Western Mediterranean",
      "departure_date": "2026-09-12",
      "return_date": "2026-09-19",
      "duration_days": 8,
      "nights": 7,
      "round_trip": true,
      "embark_port": "Barcelona",
      "disembark_port": "Barcelona",
      "region": "Western Mediterranean",
      "price_amount": 799,
      "price_currency": "USD",
      "price_per_night": 114.14,
      "itinerary": [
        { "day": 1, "port": "Barcelona", "country": "Spain" },
        { "day": 2, "port": "Marseille", "country": "France" }
      ],
      "scraped_at": "2026-06-28T04:12:00Z"
    }
  ],
  "total": 1843,
  "limit": 1,
  "offset": 0
}
```

### CSV export

```bash
curl -H "x-api-key: $CRUISEFEED_API_KEY" \
  "https://api.cruisefeed.io/cruises.csv?region=Caribbean&max_price=1200" -o cruises.csv
```

### Price-drop tracking

```bash
# fares that changed since a date (great for deal alerts)
curl -H "x-api-key: $CRUISEFEED_API_KEY" \
  "https://api.cruisefeed.io/changes?since=2026-06-20&cruise_line=MSC%20Cruises"
```

## Code examples

Runnable scripts live in [`examples/`](examples/):

- [`examples/quickstart.sh`](examples/quickstart.sh) — curl, every endpoint
- [`examples/python_example.py`](examples/python_example.py) — paginate `/cruises` with `requests`
- [`examples/node_example.js`](examples/node_example.js) — fetch + filter in Node 18+

```python
import os, requests

r = requests.get(
    "https://api.cruisefeed.io/cruises",
    headers={"x-api-key": os.environ["CRUISEFEED_API_KEY"]},
    params={"region": "Alaska", "min_nights": 7, "limit": 50},
    timeout=30,
)
for c in r.json()["items"]:
    print(c["departure_date"], c["cruise_line"], c["title"], f'${c["price_amount"]}')
```

## Data schema

| Field | Type | Notes |
|-------|------|-------|
| `source`, `source_id` | string | Natural key (unique per sailing) |
| `cruise_line`, `ship_name`, `title` | string | Normalized names |
| `departure_date`, `return_date` | date | `YYYY-MM-DD` |
| `duration_days`, `nights` | integer | |
| `round_trip` | boolean | |
| `embark_port`, `disembark_port`, `region` | string | |
| `price_amount`, `price_currency`, `price_per_night` | number/string | Lead-in fare |
| `itinerary` | array | `{ day, port, country }` per stop |
| `scraped_at` | datetime | ISO 8601 |

## Use cases

- **OTAs & cruise booking sites** — power on-site search and listings with broad,
  fresh inventory instead of scraping each line.
- **Travel agencies & host networks** — one searchable dataset across every line.
- **Aggregators & travel-tech** — a normalized cruise feed as a product input.
- **Deal & content sites** — programmatic listing pages and fare-drop alerts from
  `/changes` and price history.

## Plans

Snapshot, Sync and Managed tiers (monthly export → daily refresh + API + history +
S3/warehouse delivery). See **https://cruisefeed.io** for current pricing, and email
**support@cruisefeed.io** for a free sample export of your target lines and region.

## FAQ

**Is there a free sample?** Yes — email support@cruisefeed.io with the lines/region you
care about and we'll send a sample export before you pay.

**What formats?** JSON and CSV via REST today; S3 / data-warehouse delivery on higher plans.

**How fresh is the data?** Monthly, weekly or daily depending on plan. Each record
includes `scraped_at`, and price history is available for change tracking.

**Does it include personal data?** No — public cruise inventory facts only.

---

© CruiseFeed · [cruisefeed.io](https://cruisefeed.io) · support@cruisefeed.io
The example code in this repo is MIT-licensed; the data itself is licensed under the
CruiseFeed subscription terms.
