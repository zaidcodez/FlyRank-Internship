import unittest
from pathlib import Path

from src.scraper import PoliteScraper


ROOT = Path(__file__).resolve().parents[1]


class ScraperTests(unittest.TestCase):
    def setUp(self):
        self.scraper = PoliteScraper(ROOT)

    def test_price_normalization(self):
        raw = {
            "price_text": "£51.77",
        }
        result = self.scraper.normalize(raw)
        self.assertEqual(result["price_gbp"], 51.77)

    def test_relative_url(self):
        from urllib.parse import urljoin
        self.assertEqual(
            urljoin(
                "https://books.toscrape.com/catalogue/page-1.html",
                "../book/index.html",
            ),
            "https://books.toscrape.com/book/index.html",
        )

    def test_missing_description_is_none(self):
        html = """
        <div class="product_main">
          <h1>Example</h1>
          <p class="price_color">£10.00</p>
          <p class="availability">In stock</p>
          <p class="star-rating Two">x</p>
        </div>
        """
        soup = self.scraper.soup(html)
        description = soup.select_one("#product_description + p")
        self.assertIsNone(description)

    def test_duplicate_urls(self):
        urls = [
            "https://books.toscrape.com/catalogue/a/index.html",
            "https://books.toscrape.com/catalogue/a/index.html",
        ]
        self.assertEqual(len(set(urls)), 1)

    def test_malformed_fixture_has_no_required_title(self):
        html = "<html><body><div>not a book</div></body></html>"
        soup = self.scraper.soup(html)
        self.assertIsNone(soup.select_one("div.product_main h1"))


if __name__ == "__main__":
    unittest.main()
