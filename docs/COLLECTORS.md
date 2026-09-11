# Collectors

## Scope

Spec 003 introduces controlled acquisition of public web material. It does not introduce browser automation, login bypass, private APIs, credential scraping or unrestricted crawling.

## Command

```bash
pg-researcher collect source x_princeguttreal --output data/evidence/x-profile.json
```

For registry entries whose canonical URL is intentionally unresolved, provide a verified URL explicitly:

```bash
pg-researcher collect source spotify_prince_gutt \
  --url https://open.spotify.com/artist/... \
  --output data/evidence/spotify-profile.json
```

## Fetch policy

`config/fetch-policy.yaml` controls:

- user agent;
- timeout;
- retry count and exponential backoff;
- minimum interval between requests to the same host;
- cache TTL;
- maximum response size;
- accepted textual content types.

Retries are limited to transient transport failures, HTTP 429 and 5xx responses. `Retry-After` is honored when present.

## URL safety and normalization

The collector:

- accepts only HTTP/HTTPS;
- rejects embedded credentials;
- rejects localhost, `.local`, loopback/private/link-local/reserved literal IPs;
- removes fragments and common tracking parameters;
- normalizes default ports and query ordering.

This is a defensive application-level guard, not a substitute for network egress controls in a hostile runtime.

## Cache

The default cache lives at `.pg-researcher/cache/` and is ignored by Git. Entries are keyed by canonical URL and retain the captured response metadata/text for the configured TTL.

Use `--refresh` to bypass cache when a fresh observation is required.

## Evidence generation

Collectors do not manufacture claims. They create `Evidence` records from the captured page:

```text
public response -> normalized page -> concise observation/excerpt -> Evidence
```

Evidence IDs are content-addressed from source id, final canonical URL and normalized page text. Unchanged content therefore yields the same evidence ID even when captured again.

HTML handling extracts only a compact title, description and text excerpt. Scripts/styles are excluded. This intentionally avoids storing full third-party articles as research output.

## Adapter strategy

In this phase, official social pages, DSP pages, distributor/publisher pages and press pages share the same controlled web collector because the evidentiary contract is identical. Platform-specific API adapters should only be added when they provide stable, authorized structured metadata that cannot be obtained reliably from the public page.

## Testing

All network behavior is tested with `httpx.MockTransport`; CI performs no live source requests.
