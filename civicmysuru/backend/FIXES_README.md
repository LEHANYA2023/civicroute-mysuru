# CivicMysuru -- Fixes Applied (read this first)

This is your project with the integration gap closed and the brief's core
"twist" addressed. Everything else (your UI, styling, FastAPI structure) is
untouched. Diff summary at the bottom.

## The one sentence version

Your frontend (`script.js`) never called your backend (FastAPI). It had its
own copy of the routing/priority/duplicate logic and stored everything in
`localStorage`. Your actual backend worked fine the whole time -- it just
had no one talking to it. That's now fixed, plus two gaps against the brief.

## How to run it (both halves, every time)

**Terminal 1 -- backend:**
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend now live at `http://127.0.0.1:8000` (docs at `/docs`).

**Terminal 2 -- frontend (do NOT just double-click index.html):**
```bash
python3 -m http.server 5500
```
Open `http://127.0.0.1:5500/index.html`. Serving it over HTTP (not
`file://`) avoids browser quirks with the API calls.

If you deploy the backend somewhere other than `127.0.0.1:8000`, change the
one line `const API_BASE = "..."` near the top of `script.js`.

## What was actually broken

1. **Frontend/backend never connected.** Confirmed by testing: I ran your
   FastAPI backend directly and it worked perfectly on every endpoint
   (health, create, list, stats, route-preview, duplicate detection all
   correct). The bug wasn't a crash -- it's that `script.js` had zero
   `fetch()` calls anywhere in it. Fixed: every form submission, dashboard
   load, status change, and routing preview now calls the real API
   (`pages` in `script.js` search for `apiGet` / `apiPost` / `apiPatch`).

2. **Jurisdiction routing was a hardcoded static dict, exactly what the
   brief's "twist" warns against.** `jurisdiction_engine.py` used to say
   "Hootagalli -> Local Civic Authority" as a fixed fact. Real Mysuru has
   Hootagalli (and others) actively being absorbed into the City
   Corporation on a real date. Fixed: `jurisdiction_engine.py` now stores
   every area-authority mapping as a record with `valid_from`/`valid_to`,
   and routes based on *which record was in force on the complaint's
   date*. A new admin endpoint lets you simulate/perform a real boundary
   change with zero code changes or redeploys:
   `POST /api/admin/jurisdiction-change`.

3. **Unmatched areas were silently guessed** ("Relevant Local Civic
   Authority") instead of flagged. Fixed: an area/date with no matching
   jurisdiction record now returns `"UNASSIGNED -- needs manual
   jurisdiction review"` and `routing_mode: "Priority human review"`
   instead of a confident-sounding guess.

4. **No fake-evidence signal existed at all**, and the brief explicitly asks
   you to demonstrate what happens with a fake photo. Fixed: reusing the
   same image filename across two different complaints now flags the
   second one (`reused_evidence_flag`) and tanks its verification score.
   Documented honestly in the code as a placeholder for a real perceptual
   hash (pHash) once you accept actual image uploads -- right now the
   backend only ever received a filename string, not image bytes.

## The exact demo sequence for your video (proves every twist)

Run these in order against a fresh `civicmysuru.db`:

1. **Normal routing:** submit a Vijayanagar pothole complaint. Show it
   getting `Mysuru City Corporation`, a priority score, and a verification
   score.
2. **The boundary-change twist:** call
   `POST /api/admin/jurisdiction-change` with
   `{"area": "Bannur Road", "new_authority": "Mysuru City Corporation (newly absorbed)", "effective_from": "2026-01-01"}`
   (use `/docs` in the browser, it's the easiest way to show this on
   camera). Then submit a Bannur Road complaint and show it now routes to
   the Corporation -- **say out loud that no code changed and the server
   was never restarted.** This is the single most important 30 seconds of
   your video against this specific brief.
3. **Unmatched area, not a guess:** submit a complaint with area = "Other".
   Show the response says `UNASSIGNED -- needs manual jurisdiction review`
   instead of confidently naming an office.
4. **Duplicate detection:** submit two similar complaints in the same area
   about the same issue. Show the second one flagged as `duplicate: true`.
5. **Fake evidence:** submit two complaints with the same `image_name` on
   different areas/citizens. Show the second one gets
   `reused_evidence_flag: true` and a dropped verification score.

That is a complete, honest answer to every specific requirement in the
brief's screenshots -- routing, the boundary twist, verification, and
duplicate/fake detection -- from ONE coherent system.

## What's still worth being upfront about in your decision log

- Storage is SQLite, not a versioned GIS system. Fine for a hackathon MVP;
  say so.
- "Fake evidence" detection compares filenames, not real image content --
  a renamed reused photo would slip through. Say this is a placeholder for
  perceptual hashing once real image upload exists.
- Duplicate detection uses word overlap in the same area+category, not
  actual GPS distance (you don't currently collect lat/lng, only a
  free-text `location` field and an `area` dropdown). If you have time,
  adding real lat/lng (even just via the existing "detect my location"
  button, which already grabs GPS coordinates but currently only puts them
  in a text box) would meaningfully strengthen this.
- The AI Detection panel (`detectionSection` / `runAIDemo`) is filename
  keyword-matching, not real computer vision, and is honest about that in
  its own UI copy ("Prototype note..."). Don't let it get demoed as if it
  analyzes pixels -- judges who ask "how does the model work" should hear
  the honest answer, which is already in your own code comments.

## Files changed

- `jurisdiction_engine.py` -- rewritten (versioned jurisdiction records)
- `routing_engine.py` -- added `reused_evidence_check`, wired match-quality
  and reused-evidence into `build_route`
- `models.py` -- added `jurisdiction_match_quality`,
  `reused_evidence_flag`, `reused_evidence_reason` columns
- `main.py` -- added `/api/jurisdictions` and
  `/api/admin/jurisdiction-change`, wired new fields into responses
- `script.js` -- rewritten to call the backend instead of localStorage
  (submit, dashboard render, status updates, routing preview); reset
  button now honestly explains it can't clear server data
- `index.html`, `style.css`, `database.py`, `issue_classifier.py` --
  unchanged
