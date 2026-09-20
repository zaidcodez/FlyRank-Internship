from datetime import date
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

from report import get_report_data, build_html

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "report.db"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="FlyRank A8 - PDF Report Generator")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_reports_table():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


setup_reports_table()


class ReportRequest(BaseModel):
    force: bool = False


def generate_pdf(report_id: int):
    data = get_report_data()
    html = build_html(data)

    output_path = REPORTS_DIR / f"{report_id}.pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={
                "top": "18mm",
                "right": "14mm",
                "bottom": "18mm",
                "left": "14mm",
            },
        )
        browser.close()

    return output_path


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports")
def create_report(payload: ReportRequest):
    today = date.today().isoformat()

    if not payload.force:
        with get_db() as conn:
            existing = conn.execute(
                "SELECT id, path FROM reports WHERE created_at LIKE ? ORDER BY id DESC LIMIT 1",
                (f"{today}%",),
            ).fetchone()

        if existing:
            return {
                "id": existing["id"],
                "file": f"/reports/{existing['id']}/file",
            }

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO reports (path, created_at) VALUES (?, ?)",
            ("", today),
        )
        report_id = cursor.lastrowid

        output_path = generate_pdf(report_id)

        conn.execute(
            "UPDATE reports SET path = ? WHERE id = ?",
            (str(output_path.relative_to(BASE_DIR)), report_id),
        )
        conn.commit()

    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    with get_db() as conn:
        report = conn.execute(
            "SELECT id, path, created_at FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report["id"],
        "path": report["path"],
        "created_at": report["created_at"],
        "file": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    with get_db() as conn:
        report = conn.execute(
            "SELECT path FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    path = BASE_DIR / report["path"]

    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=f"sales-report-{report_id}.pdf",
    )
