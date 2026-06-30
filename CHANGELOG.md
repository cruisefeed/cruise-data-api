# Changelog

## 1.0

- First release. CruiseFeed API as an Apify **Standby** Actor: an always-on REST
  API that proxies api.cruisefeed.io. Endpoints: `/cruises`, `/cruises.csv`,
  `/cruises/{source}/{source_id}`, `/cruises/{source}/{source_id}/history`,
  `/changes`, `/ships`, `/ships/{ship_id}`, `/cruise-lines`, `/ports`, `/stats`.
- Pay-per-event billing: charged per cruise/ship record returned; single-record
  lookups and reference lists count as one. Non-paying users get a 5-record
  sample per page.
- The CruiseFeed API key is baked in as a secret env var, so callers don't need
  their own. A caller may still send their own `x-api-key` header to use a
  personal cruisefeed.io entitlement.
