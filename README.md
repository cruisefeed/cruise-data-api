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

## Run it on Apify (Standby API)

This Actor exposes the CruiseFeed API in **Apify Standby mode** - an always-on
REST API, not a batch job. Start it once and it stays warm; then send normal
`GET` requests to its **Standby URL** and get a live JSON/CSV response. **You do
not need a CruiseFeed API key** - the Actor carries one, and you pay through
Apify (pay-per-event, per record returned).

The Standby base URL looks like `https://<username>--cruise-data-api.apify.actor`.
Authenticate Apify requests with your Apify token (header `Authorization: Bearer
<APIFY_TOKEN>` or `?token=<APIFY_TOKEN>`):

```bash
# Caribbean sailings under $1,200, live through Apify Standby - no CruiseFeed key
curl "https://<username>--cruise-data-api.apify.actor/cruises?region=Caribbean&max_price=1200&limit=10" \
  -H "Authorization: Bearer $APIFY_TOKEN"

# one ship by IMO, with full specs
curl "https://<username>--cruise-data-api.apify.actor/ships/9839419" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

Every endpoint below is available on the Standby URL with the **same paths and
query parameters**. The Actor proxies them 1:1 to the CruiseFeed API.

**Billing.** Pay-per-event: you are charged per cruise/ship **record returned**.
Single-record lookups (one cruise, one ship, one history) and reference lists
(`/cruise-lines`, `/ports`) count as a single record. On the free tier, list
endpoints return a 5-record sample per page. Need the full catalogue, daily
price history or bulk/managed delivery? That is cheaper per record direct from
**https://cruisefeed.io** - this Actor is built for low-latency, on-demand
lookups inside Apify workflows and integrations.

> Prefer a one-shot bulk download to an Apify dataset instead of a live API?
> Use our batch Actor **CruiseFeed.io - Cruise Data Feed**.

---

## What's in the feed

| | |
|---|---|
| **Cruise lines & ships** | 100+ lines (Royal Caribbean, MSC, Carnival, Norwegian, Princess, Celebrity, Viking, Disney, AIDA …) with normalized names |
| **Sailings** | departure & return dates across the booking window, by ship and region |
| **Itineraries** | day-by-day ports of call with country, plus embark/disembark ports |
| **Pricing** | lead-in fare + price-per-night, with daily price/availability **history** for change tracking |
| **Ships** | 1,500+ vessels with specs: capacity, gross tonnage, length/beam, decks, cabins, builder, class, sister ships, flag |
| **Delivery** | REST JSON, CSV export, or push to your S3 / warehouse · refreshed monthly → daily by plan |

One normalized schema across all lines, deduplicated, with stable IDs. The data is
public cruise inventory only — no personal data.

## Authentication

**Every endpoint requires an API key**, sent as the `x-api-key` header — including the
reference lists (`/cruise-lines`, `/ships`, `/ports`). There are no public data routes.

```bash
curl -H "x-api-key: YOUR_API_KEY" "https://api.cruisefeed.io/cruises?limit=1"
```

Get a key at **https://cruisefeed.io**.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/cruises` | ✅ | List & filter sailings (the workhorse) |
| GET | `/cruises.csv` | ✅ | Same filters, streamed as CSV |
| GET | `/cruises/{source}/{source_id}` | ✅ | Get one sailing (enriched with its `ship`) |
| GET | `/cruises/{source}/{source_id}/history` | ✅ | Price & availability history |
| GET | `/changes` | ✅ | Recent price changes (fare-drop alerts) |
| GET | `/ships` | ✅ | List & filter ships (specs, capacity, build) |
| GET | `/ships/{imo}` | ✅ | Get one ship by IMO number |
| GET | `/cruise-lines` | ✅ | Distinct cruise line names |
| GET | `/ships` | ✅ | Distinct ship names |
| GET | `/ports` | ✅ | Distinct departure ports |

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

### Ship metadata

```bash
# search ships by name
curl -H "x-api-key: $CRUISEFEED_API_KEY" \
  "https://api.cruisefeed.io/ships?q=world%20europa"

# one ship by IMO (specs: tonnage, decks, cabins, capacity, builder, sister ships)
curl -H "x-api-key: $CRUISEFEED_API_KEY" \
  "https://api.cruisefeed.io/ships/9839419"
```

The single-cruise endpoint (`GET /cruises/{source}/{source_id}`) returns a `ship`
object inline, so you get the vessel's specs alongside the sailing in one call.

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
