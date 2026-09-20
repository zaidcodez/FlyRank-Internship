# FlyRank A8 — PDF Report Generator

A small FastAPI reporting pipeline built for FlyRank Internship Backend Track A8.

The pipeline is:

**SQL query → HTML report → Playwright PDF → store on disk → serve by link**

## Stack

- Python
- FastAPI
- SQLite
- Playwright
- Chromium

## 1. Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

## 2. Seed the database

```bash
python seed.py
```

This creates `report.db` with 200 generated orders.

The seed script clears the old rows first, so running it twice still leaves exactly 200 orders.

Check the aggregation output:

```bash
python test_report.py
```

## 3. Run the API

```bash
uvicorn app:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

## 4. Generate a report

```bash
curl -i -X POST http://localhost:8000/reports -H "Content-Type: application/json" -d "{}"
```

The first request returns `201` with an id and file link.

Example:

```json
{
  "id": 1,
  "file": "/reports/1/file"
}
```

Download it:

```bash
curl -o my-report.pdf http://localhost:8000/reports/1/file
```

Open `my-report.pdf` in a PDF viewer.

## 5. Report endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/reports` | Generate a report |
| GET | `/reports/{id}` | Get report metadata |
| GET | `/reports/{id}/file` | Download the PDF |

Unknown report ids return `404`.

The PDF itself is stored under `reports/`. API JSON responses only contain the file link; the PDF bytes are returned by the download endpoint.

## 6. Aggregation SQL

Total orders:

```sql
SELECT COUNT(*) FROM orders;
```

Total revenue:

```sql
SELECT COALESCE(SUM(amount), 0) FROM orders;
```

Top five products by revenue:

```sql
SELECT product, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 5;
```

Orders per day for the last seven days:

```sql
SELECT DATE(created_at) AS day, COUNT(*) AS orders
FROM orders
WHERE DATE(created_at) >= DATE('now', '-6 days')
GROUP BY DATE(created_at)
ORDER BY day;
```

## 7. Idempotency

The report endpoint checks whether a report already exists for the current day before generating another one. This protects against duplicate clicks or repeated requests creating unnecessary PDF files.

A real-world example is sending a report email twice because the same action was submitted more than once.

To deliberately generate a fresh report, use:

```bash
curl -i -X POST http://localhost:8000/reports \
  -H "Content-Type: application/json" \
  -d "{\"force\": true}"
```

A repeated normal request on the same day returns the existing report instead of generating another PDF.

## 8. PDF page breaks

The report intentionally contains all 200 orders so that the document spans multiple pages.

The HTML uses a real `<thead>` and print CSS:

```css
thead {
    display: table-header-group;
}

tr {
    break-inside: avoid;
    page-break-inside: avoid;
}
```

This keeps rows together and lets the table header repeat when the table continues onto another page.

## 9. Background jobs

For this assignment, PDF generation intentionally happens inside the request. For a much larger report or heavier traffic, I would move the query/render/store work into a background job so the API can return quickly while the report is generated separately.

## 10. GitHub submission checklist

- [ ] Public GitHub repository
- [ ] At least 7 meaningful commits
- [ ] `report.db` ignored
- [ ] Generated PDFs ignored
- [ ] README contains setup and run commands
- [ ] Aggregation SQL included
- [ ] POST → download proof included
- [ ] PDF screenshot added before submission
