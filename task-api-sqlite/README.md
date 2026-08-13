# Task API — SQLite

Week 3 version of the Task API. The API stays the same as Week 2, but tasks are now stored in SQLite.

## Run

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://localhost:8000/docs` for Swagger UI.

The first run automatically creates `tasks.db`, creates the `tasks` table, and inserts three example tasks if the table is empty.

## Database

The database file is `tasks.db`. It is ignored by Git so a fresh clone creates its own database automatically.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/tasks` | List tasks |
| GET | `/tasks/{id}` | Get one task |
| POST | `/tasks` | Create a task |
| PUT | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |

## SQL queries

```sql
SELECT * FROM tasks;
SELECT * FROM tasks WHERE done = 1;
SELECT COUNT(*) FROM tasks;
UPDATE tasks SET done = 1;
DELETE FROM tasks WHERE done = 1;
```

After changing the database manually, use `GET /tasks` in Swagger to see the changes.

## What changed?

The API did not change. The task storage changed from a Python list to SQLite. Because the data is now stored in `tasks.db`, tasks survive server restarts.

## Stage commits

```text
Stage 0: create SQLite database
Stage 1: database read endpoints
Stage 2: insert into database
Stage 3: update and delete with SQL
Stage 4: explored SQLite
Stage 5: database documentation
```
