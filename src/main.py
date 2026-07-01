"""CruiseFeed API - Standby Actor.

Exposes a normalized cruise-data API as an always-on REST API on the Apify
platform using Actor Standby mode. Instead of running a batch job and waiting
for a dataset, callers hit this Actor's standby URL like a normal HTTP API and
get a live JSON/CSV response - cruise lines, ships, sailing dates, day-by-day
itineraries, ports of call, lead-in pricing and price history, normalized into
one schema across 60+ cruise lines.

The Actor holds the upstream data-API key, so callers don't need one of their
own - they pay through Apify (pay-per-event, per record returned). This is an
unofficial Actor and is not affiliated with any cruise line; it serves public
cruise inventory data only.

Endpoints (all proxied to the upstream data API):

    GET /cruises                              list & filter sailings
    GET /cruises.csv                          same filters, CSV export
    GET /cruises/{source}/{source_id}         one sailing (+ matched ship)
    GET /cruises/{source}/{source_id}/history price history for a sailing
    GET /changes                              recent price changes
    GET /ships                                list & filter ships (specs)
    GET /ships/{ship_id}                      one ship by IMO
    GET /cruise-lines                         distinct cruise line names
    GET /ports                                distinct departure ports
    GET /sources                              distinct data sources
    GET /stats                                catalogue totals by source

Each route is proxied to the versioned upstream API (e.g. /cruises -> /v1/cruises).

Plus operational routes served locally (never billed):

    GET /            usage help (and the Apify standby readiness probe)
    GET /healthz     liveness check
"""

from __future__ import annotations

import json
import os

import httpx
import uvicorn
from apify import Actor
from fastapi import FastAPI, Request, Response

# --- Configuration ----------------------------------------------------------

# CruiseFeed data API. Overridable for self-hosted mirrors / local testing.
API_BASE = os.getenv("CRUISEFEED_API_BASE", "https://api.cruisefeed.io").strip().rstrip("/")

# The upstream data API is versioned; every proxied route is served under /v1.
API_VERSION_PREFIX = "/v1"

# CruiseFeed API key. Baked onto the Actor version as a secret env var at deploy
# time so callers never need their own. A caller may still send their own
# `x-api-key` header (e.g. a cruisefeed.io subscriber using their entitlement),
# which takes precedence.
ENV_API_KEY = os.getenv("CRUISEFEED_API_KEY", "").strip()

USER_AGENT = "cruise-data-api-actor/1.1"

# Non-paying Apify users get a small, free sample instead of full pages.
FREE_TIER_MAX_RESULTS = 5

# Pay-per-event event name. MUST match the event registered in the Actor's
# pricing, or the charge silently no-ops (earns nothing).
EVENT_RESULT = "cruise-result"

# Upstream paths this Actor will proxy. Anything else gets a local 404 so we
# never forward arbitrary requests (or bill) for unknown routes.
PROXY_PREFIXES = (
    "/cruises",
    "/changes",
    "/ships",
    "/cruise-lines",
    "/ports",
    "/sources",
    "/stats",
)

# Reference/facet lists bill as a single lookup, not one charge per name returned.
_SINGLE_CHARGE_PATHS = ("/cruise-lines", "/ports", "/sources")

# Endpoints that accept a `limit` page-size param (where the free cap applies).
LIMIT_ENDPOINTS = ("/cruises", "/cruises.csv", "/ships", "/changes")

# Hop-by-hop response headers we must not copy back to the caller.
_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-encoding",
    "content-length",
}

app = FastAPI(title="CruiseFeed API (Apify Standby)", docs_url=None, redoc_url=None)

# A single shared async client for the whole process (set in main()).
_http: httpx.AsyncClient | None = None


def _is_paying_user() -> bool:
    """Whether the run that received this request belongs to a paying Apify user."""
    return os.getenv("APIFY_USER_IS_PAYING", "").strip() == "1"


def _caller_key(request: Request) -> str:
    """A caller-supplied CruiseFeed key, from Authorization: Bearer or x-api-key."""
    auth = request.headers.get("authorization", "").strip()
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip()
    return request.headers.get("x-api-key", "").strip()


def _landing() -> dict:
    return {
        "service": "CruiseFeed API (Apify Standby)",
        "description": (
            "Real-time, normalized cruise inventory - lines, ships, sailing dates, "
            "itineraries, ports and pricing - across 60+ cruise lines. You pay per "
            "record returned via Apify pay-per-event."
        ),
        "usage": "Send a GET request to any endpoint below on this same base URL.",
        "endpoints": {
            "GET /cruises": "List & filter sailings (the workhorse).",
            "GET /cruises.csv": "Same filters, streamed as CSV.",
            "GET /cruises/{source}/{source_id}": "One sailing, enriched with its ship.",
            "GET /cruises/{source}/{source_id}/history": "Price history for a sailing.",
            "GET /changes": "Recent price changes (fare-drop alerts).",
            "GET /ships": "List & filter ships (specs, capacity, build).",
            "GET /ships/{ship_id}": "One ship by IMO number.",
            "GET /cruise-lines": "Distinct cruise line names.",
            "GET /ports": "Distinct departure ports.",
            "GET /sources": "Distinct data sources.",
            "GET /stats": "Catalogue totals by source.",
        },
        "filters_for_cruises": [
            "source", "cruise_line", "ship_name", "embark_port", "region",
            "departure_from", "departure_to", "min_price", "max_price",
            "min_nights", "max_nights", "round_trip", "dedupe", "sort",
            "include", "limit", "offset",
        ],
        "examples": [
            "/cruises?region=Caribbean&max_price=1200&limit=10",
            "/cruises?cruise_line=MSC%20Cruises&min_nights=7",
            "/changes?since=2026-06-20",
            "/ships?q=world%20europa",
        ],
        "billing": "Pay-per-event: charged per cruise/ship record returned. Lookups and reference lists count as one.",
        "note": "Unofficial API; public cruise data only. Not affiliated with any cruise line.",
    }


def _billable_count(path: str, ctype: str, body: bytes) -> int:
    """How many records a successful response should be billed for.

    Per-record for the list/search endpoints; one for single-record lookups,
    reference lists and stats. Zero when nothing was returned.
    """
    p = path.rstrip("/")
    try:
        if "csv" in ctype or p.endswith(".csv"):
            rows = [ln for ln in body.decode("utf-8", "replace").splitlines() if ln.strip()]
            return max(0, len(rows) - 1)  # drop the header row
        data = json.loads(body)
    except Exception:  # noqa: BLE001 - never let billing math break a response
        return 1

    if isinstance(data, dict) and isinstance(data.get("items"), list):
        # Facet/reference lists (also enveloped now) are a single lookup.
        if any(p.endswith(s) for s in _SINGLE_CHARGE_PATHS):
            return 1
        return len(data["items"])  # /cruises, /ships, /changes
    if isinstance(data, list):
        return len(data)  # defensive: any un-enveloped array
    return 1  # single object: one cruise / ship / history / stats


async def _charge(count: int) -> None:
    """Charge for `count` records. Best-effort: billing must never 500 a request."""
    if count <= 0:
        return
    try:
        await Actor.charge(event_name=EVENT_RESULT, count=count)
    except Exception as exc:  # noqa: BLE001
        Actor.log.warning(f"charge failed for {count} record(s): {exc}")


def _clamp_free_tier(path: str, params: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Cap page size for non-paying users so the free tier returns a sample."""
    if _is_paying_user():
        return params
    if not any(path.rstrip("/").endswith(e) or path == e for e in LIMIT_ENDPOINTS):
        return params
    out = [(k, v) for (k, v) in params if k.lower() != "limit"]
    requested = next((v for (k, v) in params if k.lower() == "limit"), None)
    try:
        capped = min(int(requested), FREE_TIER_MAX_RESULTS) if requested else FREE_TIER_MAX_RESULTS
    except (TypeError, ValueError):
        capped = FREE_TIER_MAX_RESULTS
    out.append(("limit", str(max(1, capped))))
    return out


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/{path:path}")
async def proxy(path: str, request: Request) -> Response:
    full_path = "/" + path

    # Root: the Apify standby readiness probe + a usage help page. Never billed.
    if full_path == "/":
        if "x-apify-container-server-readiness-probe" in request.headers:
            return Response(content="ok", media_type="text/plain")
        return Response(
            content=json.dumps(_landing(), indent=2),
            media_type="application/json",
        )

    # Only proxy known CruiseFeed routes.
    if not any(full_path == p or full_path.startswith(p + "/") or full_path.startswith(p + ".")
               for p in PROXY_PREFIXES):
        return Response(
            content=json.dumps({"detail": f"Unknown endpoint '{full_path}'. See / for the endpoint list."}),
            status_code=404,
            media_type="application/json",
        )

    assert _http is not None
    params = _clamp_free_tier(full_path, list(request.query_params.multi_items()))

    # Caller may supply their own CruiseFeed key (via Authorization: Bearer or the
    # legacy x-api-key header); otherwise use the baked-in one.
    caller_key = _caller_key(request)
    headers = {
        "Accept": "text/csv" if full_path.endswith(".csv") else "application/json",
        "User-Agent": USER_AGENT,
    }
    key = caller_key or ENV_API_KEY
    if key:
        headers["Authorization"] = f"Bearer {key}"

    # The upstream API is versioned: /cruises -> /v1/cruises.
    upstream_url = f"{API_BASE}{API_VERSION_PREFIX}{full_path}"
    try:
        upstream = await _http.get(upstream_url, params=params, headers=headers)
    except httpx.HTTPError as exc:
        Actor.log.warning(f"upstream request failed for {upstream_url}: {exc}")
        return Response(
            content=json.dumps({"detail": "Upstream CruiseFeed API is unavailable. Please retry."}),
            status_code=502,
            media_type="application/json",
        )

    ctype = upstream.headers.get("content-type", "application/json")
    body = upstream.content

    # Bill only successful data responses, by the number of records returned.
    if upstream.status_code == 200:
        await _charge(_billable_count(full_path, ctype, body))

    out_headers = {
        k: v for k, v in upstream.headers.items() if k.lower() not in _HOP_BY_HOP
    }
    return Response(content=body, status_code=upstream.status_code, media_type=ctype, headers=out_headers)


async def main() -> None:
    """Run the standby HTTP server for the lifetime of the Actor run."""
    global _http, API_BASE

    async with Actor:
        # Standard-mode runs may pass an input; standby runs use the Actor's
        # default input. Honor an apiBaseUrl override for self-hosted mirrors.
        actor_input = await Actor.get_input() or {}
        override = (actor_input.get("apiBaseUrl") or "").strip().rstrip("/")
        if override:
            API_BASE = override

        if not ENV_API_KEY:
            Actor.log.warning(
                "CRUISEFEED_API_KEY is not set - upstream requests will 401. "
                "Deploy with deploy_cruise_data_api.py to bake the key in."
            )

        meta_origin = Actor.configuration.meta_origin
        port = Actor.configuration.web_server_port
        Actor.log.info(
            f"CruiseFeed standby API starting | origin={meta_origin} | port={port}"
        )

        _http = httpx.AsyncClient(timeout=60.0)
        try:
            config = uvicorn.Config(
                app,
                host="0.0.0.0",  # noqa: S104 - must be reachable via the container URL
                port=port,
                access_log=False,
                log_level="info",
            )
            server = uvicorn.Server(config)
            await server.serve()
        finally:
            await _http.aclose()
