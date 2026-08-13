from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Task API", version="1.0")

DB_FILE = "tasks.db"


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool = False


def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)

    count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    if count == 0:
        connection.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Learn FastAPI", 0),
                ("Build a CRUD API", 0),
                ("Connect SQLite", 0),
            ],
        )

    connection.commit()
    connection.close()


def row_to_task(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


init_db()


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    db = get_connection()
    rows = db.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()
    db.close()
    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    db = get_connection()
    row = db.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    db.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return row_to_task(row)


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    title = task.title.strip()

    if not title:
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    db = get_connection()
    cursor = db.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0)
    )
    db.commit()

    row = db.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    db.close()

    return row_to_task(row)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    title = task.title.strip()

    if not title:
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    db = get_connection()

    existing = db.execute(
        "SELECT id FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    if existing is None:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")

    db.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (title, int(task.done), task_id),
    )
    db.commit()

    row = db.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    db.close()

    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    db = get_connection()
    cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    db.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return None
