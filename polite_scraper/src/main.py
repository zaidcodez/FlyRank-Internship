from pathlib import Path
from .scraper import PoliteScraper


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    inject_bad = "--test-failure" in __import__("sys").argv

    scraper = PoliteScraper(root)
    report, books, errors = scraper.run(inject_bad_url=inject_bad)

    print()
    print("Run complete.")
    print(f"catalogue_pages={report['catalogue_pages']}")
    print(f"discovered={report['discovered_urls']}")
    print(f"unique_urls={report['unique_urls']}")
    print(f"detail_pages={len(books) + len(errors)}")
    print(f"valid_records={report['valid_records']}")
    print(f"failed_pages={report['failed_pages']}")
