# The Polite Scraper — FlyRank W5 A9

A small Python scraper for the **Books to Scrape** practice sandbox. It discovers the first
three catalogue pages, visits the 60 book pages, extracts the useful fields, normalizes and
validates them, caches pages during development, and writes a run report.

## Target classification

- **Target:** https://books.toscrape.com/
- **Why this target:** Books to Scrape is a public practice sandbox made for learning web scraping.
- **Scope:** first 3 catalogue pages only; 60 unique book pages.
- **Data collected:** title, product URL, price, availability, rating, description, source page,
  and fetch timestamp.
- **Why appropriate:** this is a dedicated scraping practice site, so the assignment does not
  require scraping a normal production site.

### robots.txt check

`https://books.toscrape.com/robots.txt` was checked before coding. The scraper's target is still
limited to the dedicated Books to Scrape sandbox and this repository does not reuse the code for
other sites.

> I will not reuse this code on another site without checking its rules and terms first.

## Lane

Python 3.10+ using Requests, Beautiful Soup, and Pydantic.

## Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
python -m src.main
```

The first run downloads the catalogue/detail pages. Later development runs use the cached HTML.

## Schema

A finished record contains:

- `title`
- `product_url`
- `price_text`
- `price_gbp`
- `availability_text`
- `rating_text`
- `description`
- `source_page`
- `fetched_at`

Good records go to `output/books.json`. Records that fail validation go to `output/errors.json`.

## Politeness rules

- Identifying user-agent
- 10 second request timeout
- Status checked before parsing
- At least 500 ms between real requests
- Cached pages are read locally and do not cause another request
- Failed 5xx/timeout requests are retried once
- 403 and 404 are not retried
- Only the first three catalogue pages are followed

## Idempotency

Records are keyed by their canonical product URL before writing. Running the scraper again does
not append duplicate books.

## Honest limitation

The parser depends on the current HTML structure of Books to Scrape. If the site's markup changes,
selectors may need updating.

## Browser note

The core assignment does not need a browser because the book data is already present in the HTML
returned by the server. A browser would add overhead without helping this part of the task.

## Ethics

Use an official API when one exists. Never bypass logins, paywalls, or blocks. Collect only what
is needed, respect site rules, and keep request rates reasonable.

## Sample run report

After a successful run, `output/run-report.json` records the start time, duration, fetches,
cache hits, valid/invalid records, and failed pages.

## Tests

```bash
python -m unittest discover -s tests -v
```
