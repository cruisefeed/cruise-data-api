#!/usr/bin/env node
/**
 * CruiseFeed API — Node example (Node 18+, uses built-in fetch).
 *
 *   export CRUISEFEED_API_KEY=...        // Windows: set CRUISEFEED_API_KEY=...
 *   node node_example.js
 */

const BASE = "https://api.cruisefeed.io";

async function getCruises(filters = {}) {
  const key = process.env.CRUISEFEED_API_KEY;
  if (!key) {
    console.error("Set CRUISEFEED_API_KEY in your environment.");
    process.exit(1);
  }
  const out = [];
  let offset = 0;
  const page = 200;
  for (;;) {
    const params = new URLSearchParams({ ...filters, limit: page, offset });
    const res = await fetch(`${BASE}/cruises?${params}`, {
      headers: { "x-api-key": key },
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    const body = await res.json();
    out.push(...body.items);
    offset += body.items.length;
    if (body.items.length < page || offset >= (body.total ?? 0)) break;
  }
  return out;
}

(async () => {
  const cruises = await getCruises({ region: "Caribbean", max_price: 1200, min_nights: 5 });
  console.log(`${cruises.length} Caribbean sailings (5+ nights, <= $1200)\n`);
  for (const c of cruises.slice(0, 10)) {
    const ports = (c.itinerary || []).map((s) => s.port).join(" > ");
    console.log(
      `${c.departure_date}  ${c.cruise_line.padEnd(18)} ${c.title.padEnd(28)} ` +
        `$${String(c.price_amount).padEnd(6)} ${ports}`
    );
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
