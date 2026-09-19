<<<<<<< HEAD
# civicroute-mysuru
Time-aware civic complaint routing system for Mysusru
=======
# CivicMysuru — Full Stack (Frontend + Backend)

A citizen complaint reporting and routing platform for Mysuru. Frontend is
static HTML/CSS/JS; backend is FastAPI + SQLite. They are two separate
processes that talk over HTTP — run both at the same time.

## Folder structure

```
civicmysuru/
├── backend/
│   ├── main.py                 # FastAPI app — run this file directly
│   ├── database.py             # SQLite/SQLAlchemy connection
│   ├── models.py                # Complaint table schema
│   ├── routing_engine.py        # priority, verification, duplicate & fake-evidence logic
│   ├── jurisdiction_engine.py   # area → authority mapping, versioned by date
│   ├── issue_classifier.py      # rule-based demo issue classifier
│   ├── requirements.txt
│   ├── test_backend_logic.py
│   ├── README_BACKEND.MD
│   └── FIXES_README.md
│
└── frontend/
    ├── index.html                # landing page
    ├── login.html                 # demo login (any email + 4+ char password)
    ├── report.html                 # citizen complaint form + live routing preview
    ├── dashboard.html               # complaint queue, stats, status updates
    ├── detect.html                   # standalone AI detection demo (upload → classify)
    ├── css/
    │   └── style.css
    └── js/
        ├── common.js               # API_BASE, theme toggle, session pill, toasts
        ├── auth.js                  # login form handler
        ├── dashboard.js              # loads/filters complaints, updates status
        ├── report.js                 # live route preview, AI classify, submit
        └── detect.js                  # calls /api/classify-issue, hands off to report.html
```

## How to run it (two terminals, every time)

**Terminal 1 — backend**

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Runs at `http://127.0.0.1:8000`. Interactive API docs at `/docs`. A
`civicmysuru.db` SQLite file is created automatically on first run.

**Terminal 2 — frontend**

```bash
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500/index.html` in your browser.

> You must serve the frontend over `http://`, not open the HTML files
> directly as `file://`, or the browser's fetch calls to the backend will
> misbehave in some browsers.

## Why this "just works" together

- `frontend/js/common.js` hardcodes `API_BASE = "http://127.0.0.1:8000"` —
  matches exactly where `python main.py` serves.
- The backend's CORS middleware allows all origins (`allow_origins=["*"]`),
  so the frontend on port 5500 can call the backend on port 8000 with no
  extra configuration.
- Every endpoint the frontend JS calls (`/api/complaints`, `/api/stats`,
  `/api/route-preview`, `/api/classify-issue`,
  `/api/complaints/{id}/status`) exists in `backend/main.py` with the exact
  same request/response shape the JS expects.

## Before your demo/deployment

- If you deploy the frontend and backend on different real domains, update
  `API_BASE` in `frontend/js/common.js` to the backend's deployed URL, and
  tighten `allow_origins` in `backend/main.py` from `"*"` to that exact
  frontend URL.
>>>>>>> 5a2e014 (Initial commit)
