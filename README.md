# CruiseFeed API – Real-Time Cruise Data & Pricing (Standby REST API)

An always-on REST API for **normalized cruise inventory** – cruise lines, ships,
sailing dates, day-by-day itineraries, ports of call and lead-in pricing –
across 60+ cruise lines, in one clean schema. It runs on Apify in **Standby
mode**, so you query it live like an API instead of running a batch job. Every
record carries a stable opaque `id` and the same shape
across every line.

It's built for travel-tech use cases – OTAs, cruise-comparison sites, travel
agencies and data aggregators – that need broad, fresh cruise inventory on
demand. The data is **public cruise inventory only – no personal data.**

> **Unofficial.** This Actor is not affiliated with, endorsed by, or sponsored
> by any cruise line or travel brand. Cruise line and ship names are trademarks
> of their respective owners and are used here only to describe the data the
> Actor returns.

## How it works (Standby)

This Actor is a live HTTP API, not a one-off run. Start it once and it stays
warm; then send normal `GET` requests to its **Standby URL**:

```
https://<username>--cruise-data-api.apify.actor/<endpoint>
```

- **Authentication is handled by Apify.** Send your Apify token as
  `Authorization: Bearer <APIFY_TOKEN>` or `?token=<APIFY_TOKEN>`. From the
  **Standby** tab on this page you can also try every endpoint right in the
  browser, no token setup required.
- **Billing is pay-per-event** (see [Billing](#billing)).
- The interactive endpoint reference is on the **Standby** tab (rendered from the
  Actor's OpenAPI schema).

```bash
# Caribbean sailings under $1,200, live
curl "https://<username>--cruise-data-api.apify.actor/cruises?region=Caribbean&max_price=1200&limit=10" \
  -H "Authorization: Bearer $APIFY_TOKEN"

# one ship by IMO number, with full specs
curl "https://<username>--cruise-data-api.apify.actor/ships/9837420" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cruises` | List & filter sailings (the workhorse) |
| GET | `/cruises.csv` | Same filters, streamed as CSV |
| GET | `/cruises/{id}` | One sailing, enriched with its `ship` |
| GET | `/cruises/{id}/history` | Price & availability history |
| GET | `/changes` | Recent price changes (fare-drop alerts) |
| GET | `/ships` | List & filter ships (specs, capacity, build) |
| GET | `/ships/{ship_id}` | One ship by IMO number |
| GET | `/cruise-lines` | Distinct cruise line names |
| GET | `/ports` | Distinct departure ports |
| GET | `/stats` | Catalogue totals |

Each cruise carries a lead-in `price_amount`, plus a `fares` array that holds the
per-cabin-class breakdown **when the source publishes more than one cabin fare** —
it's empty when the line quotes only a single "from" price.

### Machine-readable spec & Postman

- **OpenAPI:** [`openapi.yaml`](openapi.yaml) — kept in lock-step with the live API.
- **Postman:** [`cruisefeed.postman_collection.json`](cruisefeed.postman_collection.json) —
  import it, set the `apiKey` variable, and every request is pre-wired. It targets the
  **direct hosted API** at `https://api.cruisefeed.io` (auth: `Authorization: Bearer <key>`),
  which is the same data as this Actor via a different front door.
- **Interactive docs:** https://api.cruisefeed.io/docs

### Filters for `GET /cruises`

`cruise_line` · `ship_name` · `embark_port` · `region` (partial) ·
`departure_from` · `departure_to` · `min_price` · `max_price` · `min_nights` ·
`max_nights` · `round_trip` · `dedupe` (default true) · `include_past` (default
false) · `sort` · `limit` (1–500, default 50) · `offset`.

`sort` accepts exactly `departure_date` (default), `-departure_date`, `price`,
`-price` — a `-` prefix means descending, and anything else is a `400`. There is
no `price_amount` sort, despite the response field being called `price_amount`.

The listing returns **upcoming sailings only**; the catalogue reaches back to
2015 and ~98% of departed sailings carry no price. Pass `include_past=true` for
history, or set `departure_from` / `departure_to` to take control of the window.

## Example: list cruises

**Request**

```bash
curl "https://<username>--cruise-data-api.apify.actor/cruises?cruise_line=MSC%20Cruises&min_price=1&min_nights=5&limit=1" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

**Response** (a real record, itinerary trimmed to two stops — note how much of a
typical sailing is `null`)

```json
{
  "items": [
    {
      "id": "cru_27fad303985bed3f",
      "cruise_line": "MSC Cruises",
      "ship_name": "MSC Seaview",
      "title": "7 days, round-trip Mediterranean",
      "departure_date": "2026-06-01",
      "return_date": "2026-06-08",
      "duration_days": 7,
      "nights": 7,
      "round_trip": true,
      "embark_port": "Palermo, Sicily Italy",
      "disembark_port": "Palermo, Sicily Italy",
      "region": "Mediterranean",
      "ship_code": null,
      "destination_code": null,
      "sea_days": 0,
      "port_count": 6,
      "price_amount": 1028.0,
      "price_currency": "USD",
      "price_per_night": 146.86,
      "taxes_and_fees": null,
      "taxes_currency": null,
      "obc_amount": null,
      "sold_out": null,
      "fares": [],
      "itinerary": [
        {
          "seq": 1, "day_number": 1, "date": "2026-06-01",
          "port": "Palermo, Sicily Italy", "date_raw": "01 Jun 20:00",
          "arrive": null, "depart": "01 Jun 20:00",
          "is_embark": true, "is_disembark": false, "is_sea_day": false
        },
        {
          "seq": 2, "day_number": 3, "date": "2026-06-03",
          "port": "Ibiza, Ibiza Island Balearic Spain",
          "date_raw": "03 Jun 11:30 - 23:00", "arrive": "03 Jun 11:30",
          "depart": "23:00", "is_embark": false, "is_disembark": false,
          "is_sea_day": false
        }
      ],
      "booking_url": null,
      "detail_url": null,
      "image_url": null,
      "scraped_at": "2026-07-12T04:04:32.444119"
    }
  ],
  "total": 6122,
  "limit": 1,
  "offset": 0
}
```

### CSV export

```bash
curl "https://<username>--cruise-data-api.apify.actor/cruises.csv?region=Caribbean&max_price=1200" \
  -H "Authorization: Bearer $APIFY_TOKEN" -o cruises.csv
```

### Price-drop tracking

```bash
# fares that changed since a date (great for deal alerts)
curl "https://<username>--cruise-data-api.apify.actor/changes?since=2026-06-20&cruise_line=MSC%20Cruises" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

### Ship metadata

```bash
# search ships by name
curl "https://<username>--cruise-data-api.apify.actor/ships?q=world%20europa" \
  -H "Authorization: Bearer $APIFY_TOKEN"

# one ship by IMO (tonnage, decks, cabins, capacity, builder, sister ships)
curl "https://<username>--cruise-data-api.apify.actor/ships/9837420" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

The single-cruise endpoint (`GET /cruises/{id}`) returns a `ship`
object inline, so you get the vessel's specs alongside the sailing in one call.

## Billing

Pay-per-event, charged through Apify:

- **Per record returned** by the list/search endpoints (`/cruises`, `/ships`,
  `/changes`, CSV rows).
- **One record** for single-record lookups (one cruise, one ship, one history
  document) and for reference lists (`/cruise-lines`, `/ports`, `/stats`).
- A small fixed **Actor start** fee when a Standby instance spins up.

On the free tier, list endpoints return a **5-record sample per page** so you can
evaluate the data before committing. See the **Pricing** section on this page for
current rates.

## Data schema

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Opaque, source-agnostic id (unique per sailing) |
| `cruise_line`, `ship_name`, `title` | string | Normalized names |
| `departure_date`, `return_date` | date | `YYYY-MM-DD` (may be null for product-level sailings) |
| `duration_days`, `nights` | integer | |
| `round_trip` | boolean | |
| `embark_port`, `disembark_port`, `region` | string | |
| `ship_code`, `destination_code` | string | Line-specific codes, when exposed |
| `sea_days`, `port_count` | integer | Days at sea / ports of call on the itinerary |
| `price_amount`, `price_currency`, `price_per_night` | number | Lead-in fare (may be null) |
| `taxes_and_fees`, `taxes_currency` | number/string | Taxes & fees when itemized |
| `obc_amount` | number | Bundled onboard credit, when advertised |
| `sold_out` | boolean | Listed but no longer bookable |
| `fares` | array | Per-cabin-class breakdown (partial across lines) |
| `itinerary` | array | `{ seq, port, date_raw, is_embark, is_disembark }` per stop |
| `booking_url`, `detail_url`, `image_url` | string | Deep links and a representative image |
| `scraped_at` | datetime | ISO 8601 |

The `/ships` endpoints add vessel specs: IMO, operator, year built, capacity,
gross tonnage, length/beam, decks, cabins, builder, class, sister ships and flag.

## Use cases

- **OTAs & cruise booking sites** – power on-site search and listings with broad,
  fresh inventory instead of scraping each line.
- **Travel agencies & host networks** – one searchable dataset across every line.
- **Aggregators & travel-tech** – a normalized cruise feed as a product input.
- **Deal & content sites** – programmatic listing pages and fare-drop alerts from
  `/changes` and price history.

## FAQ

**How fresh is the data?** Inventory and prices are refreshed regularly; each
record includes a `scraped_at` timestamp, and price history is available for
change tracking via `/changes` and `/cruises/{id}/history`.

**What formats?** JSON for every endpoint, plus CSV via `/cruises.csv`.

**Does it include personal data?** No – public cruise inventory facts only
(lines, ships, sailings, itineraries, ports, lead-in prices).

**Is it official?** No. It is an independent, unofficial Actor and is not
affiliated with any cruise line. Brand names are used only to describe the data.

## Support

Questions, bugs or feature requests? Use the **Issues** tab on this Actor's page.
