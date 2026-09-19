# CivicMysuru Backend

FastAPI + SQLite backend for the CivicMysuru civic complaint routing MVP.

## Files

- `main.py` — FastAPI application and API endpoints
- `database.py` — SQLite/SQLAlchemy connection
- `models.py` — Complaint database model
- `routing-engine.py` — issue, priority, verification and duplicate logic
- `jurisdiction_engine.py` — prototype area/time routing
- `issue_classifier.py` — explainable demo issue classifier
- `requirements.txt` — Python dependencies

## Run locally

From this folder, install dependencies once:

```bash
pip install -r requirements.txt
```

Then start the server with a single command, on any OS:

```bash
python main.py
```

(Windows users: use `python main.py`; macOS/Linux users can use `python3 main.py` if `python` isn't aliased.)

This runs the exact same app as `uvicorn main:app --reload` — that command still works too if you prefer it — but `python main.py` is now enough on its own, with auto-reload already enabled.

The API will be available at:

- `http://127.0.0.1:8000`
- Interactive API docs: `http://127.0.0.1:8000/docs`

A `civicmysuru.db` SQLite file is created automatically.

## Main endpoints

### Health

`GET /api/health`

### Create complaint

`POST /api/complaints`

Example JSON:

```json
{
  "citizen_name": "Demo Citizen",
  "area": "Vijayanagar",
  "issue_type": "Pothole",
  "location": "Main Road",
  "description": "Large pothole causing danger to two-wheelers.",
  "image_name": "pothole.jpg"
}
```

### List complaints

`GET /api/complaints`

Optional filters:

- `search`
- `status`
- `priority`

### Get one complaint

`GET /api/complaints/{complaint_id}`

### Update status

`PATCH /api/complaints/{complaint_id}/status`

```json
{
  "status": "In Progress"
}
```

Allowed values:

- `Open`
- `In Progress`
- `Resolved`

### Dashboard statistics

`GET /api/stats`

#Routing preview

`GET /api/route-preview?area=Vijayanagar&issue_type=Pothole&description=Large%20pothole`

#Demo issue classification

`POST /api/classify-issue`

```json
{
  "filename": "garbage_dump.jpg",
  "description": "Large garbage dump near road"
}
```


