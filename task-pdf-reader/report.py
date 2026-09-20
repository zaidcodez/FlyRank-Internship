from datetime import date
import sqlite3
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "report.db"


def get_report_data():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        total_revenue = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM orders"
        ).fetchone()[0]

        top_products = conn.execute("""
            SELECT product, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
            FROM orders
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5
        """).fetchall()

        orders_per_day = conn.execute("""
            SELECT DATE(created_at) AS day, COUNT(*) AS orders
            FROM orders
            WHERE DATE(created_at) >= DATE('now', '-6 days')
            GROUP BY DATE(created_at)
            ORDER BY day
        """).fetchall()

        all_orders = conn.execute("""
            SELECT id, customer, product, amount, created_at
            FROM orders
            ORDER BY created_at DESC, id DESC
        """).fetchall()

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "top_products": [dict(row) for row in top_products],
        "orders_per_day": [dict(row) for row in orders_per_day],
        "all_orders": [dict(row) for row in all_orders],
    }


def build_html(data):
    product_rows = "".join(
        f"""
        <tr>
            <td>{escape(row["product"])}</td>
            <td>{row["orders"]}</td>
            <td>${row["revenue"]:.2f}</td>
        </tr>
        """
        for row in data["top_products"]
    )

    day_rows = "".join(
        f"""
        <tr>
            <td>{escape(row["day"])}</td>
            <td>{row["orders"]}</td>
        </tr>
        """
        for row in data["orders_per_day"]
    )

    order_rows = "".join(
        f"""
        <tr>
            <td>{row["id"]}</td>
            <td>{escape(row["customer"])}</td>
            <td>{escape(row["product"])}</td>
            <td>${row["amount"]:.2f}</td>
            <td>{escape(row["created_at"])}</td>
        </tr>
        """
        for row in data["all_orders"]
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Sales Report</title>
<style>
    @page {{
        size: A4;
        margin: 18mm 14mm;
    }}

    * {{
        box-sizing: border-box;
    }}

    body {{
        font-family: Arial, sans-serif;
        color: #222;
        font-size: 10px;
        margin: 0;
    }}

    h1 {{
        margin: 0 0 4px;
        font-size: 24px;
    }}

    h2 {{
        margin: 24px 0 8px;
        font-size: 15px;
        border-bottom: 1px solid #ddd;
        padding-bottom: 5px;
    }}

    .date {{
        color: #666;
        margin-bottom: 18px;
    }}

    .summary {{
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }}

    .card {{
        flex: 1;
        border: 1px solid #ddd;
        padding: 12px;
        border-radius: 5px;
    }}

    .label {{
        color: #666;
        font-size: 9px;
        text-transform: uppercase;
    }}

    .value {{
        font-size: 18px;
        font-weight: bold;
        margin-top: 5px;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 14px;
    }}

    th, td {{
        border: 1px solid #ddd;
        padding: 5px 6px;
        text-align: left;
    }}

    th {{
        background: #f2f2f2;
        font-weight: bold;
    }}

    thead {{
        display: table-header-group;
    }}

    tr {{
        break-inside: avoid;
        page-break-inside: avoid;
    }}

    .number {{
        text-align: right;
    }}
</style>
</head>
<body>
    <h1>Sales Report</h1>
    <div class="date">Generated on {date.today().isoformat()}</div>

    <div class="summary">
        <div class="card">
            <div class="label">Total Orders</div>
            <div class="value">{data["total_orders"]}</div>
        </div>
        <div class="card">
            <div class="label">Total Revenue</div>
            <div class="value">${data["total_revenue"]:.2f}</div>
        </div>
    </div>

    <h2>Top Products by Revenue</h2>
    <table>
        <thead>
            <tr>
                <th>Product</th>
                <th>Orders</th>
                <th>Revenue</th>
            </tr>
        </thead>
        <tbody>{product_rows}</tbody>
    </table>

    <h2>Orders Per Day — Last 7 Days</h2>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Orders</th>
            </tr>
        </thead>
        <tbody>{day_rows}</tbody>
    </table>

    <h2>All Orders</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Customer</th>
                <th>Product</th>
                <th>Amount</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>{order_rows}</tbody>
    </table>
</body>
</html>"""
