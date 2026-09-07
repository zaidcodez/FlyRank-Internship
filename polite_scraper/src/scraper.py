import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import BookRecord


BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = urljoin(BASE_URL, "catalogue/page-1.html")
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/zaidcodez/Python-Learning)"
TIMEOUT = 10
DELAY_SECONDS = 0.5


class PoliteScraper:
    def __init__(self, root: Path):
        self.root = root
        self.cache_dir = root / "cache"
        self.output_dir = root / "output"
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self.fetched = 0
        self.cache_hits = 0
        self.failed_pages = []
        self.last_request_at = None

    def _wait_if_needed(self):
        if self.last_request_at is None:
            return
        elapsed = time.monotonic() - self.last_request_at
        if elapsed < DELAY_SECONDS:
            time.sleep(DELAY_SECONDS - elapsed)

    def fetch(self, url: str, cache_file: Path):
        if cache_file.exists():
            self.cache_hits += 1
            print(f"CACHE HIT {url} ({cache_file.stat().st_size} bytes)")
            return cache_file.read_text(encoding="utf-8"), False

        attempts = 2
        for attempt in range(1, attempts + 1):
            self._wait_if_needed()
            try:
                self.last_request_at = time.monotonic()
                response = self.session.get(url, timeout=TIMEOUT)

                if response.status_code == 200:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(response.text, encoding="utf-8")
                    self.fetched += 1
                    print(f"FETCH {url} ({len(response.content)} bytes)")
                    return response.text, True

                if response.status_code in (403, 404):
                    raise RuntimeError(f"HTTP {response.status_code}")

                if 500 <= response.status_code < 600 and attempt == 1:
                    time.sleep(1)
                    continue

                raise RuntimeError(f"HTTP {response.status_code}")

            except (requests.Timeout, requests.RequestException) as exc:
                if attempt == 1:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"{type(exc).__name__}: {exc}") from exc

        raise RuntimeError("request failed")

    @staticmethod
    def soup(html: str):
        return BeautifulSoup(html, "html.parser")

    def discover_catalogue(self):
        urls = []
        source_pages = {}

        current_url = CATALOGUE_URL
        for page_number in range(1, 4):
            cache_file = self.cache_dir / f"catalogue-page-{page_number}.html"
            html, _ = self.fetch(current_url, cache_file)
            soup = self.soup(html)

            for article in soup.select("article.product_pod"):
                link = article.select_one("h3 a")
                if not link or not link.get("href"):
                    continue
                product_url = urljoin(current_url, link["href"])
                if product_url not in source_pages:
                    source_pages[product_url] = current_url
                    urls.append(product_url)

            next_link = soup.select_one("li.next a")
            if page_number < 3 and next_link and next_link.get("href"):
                current_url = urljoin(current_url, next_link["href"])
            else:
                break

        return urls, source_pages

    def extract_book(self, product_url: str, source_page: str, index: int):
        safe_name = f"book-{index:03d}.html"
        cache_file = self.cache_dir / "books" / safe_name
        html, fetched_now = self.fetch(product_url, cache_file)
        soup = self.soup(html)

        title_node = soup.select_one("div.product_main h1")
        price_node = soup.select_one("div.product_main .price_color")
        availability_node = soup.select_one("div.product_main .availability")
        rating_node = soup.select_one("div.product_main p.star-rating")
        description_node = soup.select_one("#product_description + p")

        if not all([title_node, price_node, availability_node, rating_node]):
            raise ValueError("required product field missing")

        rating_classes = rating_node.get("class", [])
        rating = next((c for c in rating_classes if c != "star-rating"), None)

        description = description_node.get_text(" ", strip=True) if description_node else None

        fetched_at = datetime.now(timezone.utc).isoformat()
        if not fetched_now:
            # Keep the current run's provenance explicit even when content came from cache.
            fetched_at = datetime.now(timezone.utc).isoformat()

        return {
            "title": title_node.get_text(" ", strip=True),
            "product_url": product_url,
            "price_text": price_node.get_text(" ", strip=True),
            "availability_text": availability_node.get_text(" ", strip=True),
            "rating_text": rating or rating_node.get_text(" ", strip=True),
            "description": description,
            "source_page": source_page,
            "fetched_at": fetched_at,
        }

    @staticmethod
    def normalize(raw):
        price_text = (
            raw["price_text"]
            .replace("£", "")
            .replace("Â", "")
            .replace(",", "")
            .strip()
        )

        raw["price_gbp"] = float(price_text)
        return raw

    def run(self, inject_bad_url=False):
        started = time.monotonic()
        started_at = datetime.now(timezone.utc).isoformat()

        urls, source_pages = self.discover_catalogue()
        if inject_bad_url:
            urls.append(urljoin(BASE_URL, "catalogue/this-book-does-not-exist_99999/index.html"))

        valid = {}
        errors = []

        for index, url in enumerate(urls, start=1):
            try:
                source = source_pages.get(url, CATALOGUE_URL)
                raw = self.extract_book(url, source, index)
                normalized = self.normalize(raw)
                record = BookRecord.model_validate(normalized)
                valid[str(record.product_url)] = record.model_dump(mode="json")
            except Exception as exc:
                self.failed_pages.append(url)
                errors.append({"product_url": url, "reason": str(exc)})
                print(f"FAILED {url}: {exc}")

        books = list(valid.values())
        (self.output_dir / "books.json").write_text(
            json.dumps(books, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.output_dir / "errors.json").write_text(
            json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        report = {
            "started_at": started_at,
            "duration_seconds": round(time.monotonic() - started, 3),
            "catalogue_pages": 3,
            "discovered_urls": len(urls),
            "unique_urls": len(set(urls)),
            "pages_fetched": self.fetched,
            "cache_hits": self.cache_hits,
            "valid_records": len(books),
            "invalid_records": len(errors),
            "failed_pages": len(self.failed_pages),
        }
        (self.output_dir / "run-report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        return report, books, errors
