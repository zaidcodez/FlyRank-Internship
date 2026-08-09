# Task API

A small FastAPI CRUD API for a to-do list. Tasks are stored in memory, so they reset when the server restarts.

## Run

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

The API runs at:

- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/docs

## Endpoints

| Method | Endpoint | Purpose | Success |
|---|---|---|---|
| GET | `/` | API information | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/tasks` | List all tasks | 200 |
| GET | `/tasks/{id}` | Get one task | 200 |
| POST | `/tasks` | Create a task | 201 |
| PUT | `/tasks/{id}` | Update a task | 200 |
| DELETE | `/tasks/{id}` | Delete a task | 204 |

Errors:

- `400` — invalid/empty title
- `404` — task does not exist

## Example curl tests

### List tasks

```bash
curl -i http://localhost:8000/tasks
```

### Get one task

```bash
curl -i http://localhost:8000/tasks/1
```

### Test 404

```bash
curl -i http://localhost:8000/tasks/99
```

### Create

```bash
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"Buy milk\"}"
```

### Update

```bash
curl -i -X PUT http://localhost:8000/tasks/1 -H "Content-Type: application/json" -d "{\"title\":\"Learn FastAPI properly\",\"done\":true}"
```

### Delete

```bash
curl -i -X DELETE http://localhost:8000/tasks/1
```

## Swagger UI

Open `http://localhost:8000/docs` and use **Try it out** to run the complete CRUD cycle.

## Important observation

The tasks are stored only in memory. Restarting the server resets the task list to the three example tasks. This is intentional for this assignment; the database comes later.

## Git stage commits

Use one commit after each completed stage:

```text
Stage 0: hello server
Stage 1: root and health endpoints
Stage 2: read endpoints with 404
Stage 3: create with validation
Stage 4: full CRUD
Stage 5: Swagger UI
Stage 6: publish and docs
```
