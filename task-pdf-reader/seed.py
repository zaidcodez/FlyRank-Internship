from datetime import date, timedelta
import random
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "report.db"

PRODUCTS = [
    "Keyboard",
    "Mouse",
    "Headphones",
    "Webcam",
    "USB Hub",
    "Laptop Stand",
]

CUSTOMERS = [
    "Ali", "Ahmed", "Sara", "Hassan", "Ayesha",
    "Usman", "Fatima", "Hamza", "Zain", "Mariam",
]


def seed():
    random.seed(42)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS orders")
        conn.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        today = date.today()

        rows = []
        for _ in range(200):
            order_date = today - timedelta(days=random.randint(0, 29))
            rows.append((
                random.choice(CUSTOMERS),
                random.choice(PRODUCTS),
                round(random.uniform(5, 200), 2),
                order_date.isoformat(),
            ))

        conn.executemany("""
            INSERT INTO orders (customer, product, amount, created_at)
            VALUES (?, ?, ?, ?)
        """, rows)

        conn.commit()

    print("Seeded 200 orders into report.db")


if __name__ == "__main__":
    seed()
