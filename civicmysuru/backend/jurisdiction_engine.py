"""
Jurisdiction engine -- v2.

WHY THIS CHANGED FROM v1:
The original AREA_RULES dict was a single hardcoded snapshot ("Hootagalli ->
Local Civic Authority"). The hackathon brief is explicit that this is wrong
for Mysuru right now: 1 CMC + 4 Town Panchayats + 8 Gram Panchayats are being
actively absorbed into Mysuru City Corporation. A hardcoded dict can't
represent "Hootagalli belonged to a Town Panchayat until 31 March 2026, and
to Mysuru City Corporation from 1 April 2026 onward" -- and it can't be
updated by a non-engineer when the next merger happens.

THE FIX: every area-to-authority mapping is a *record* with an effective
date range, not a single value. Routing always asks "which record was in
force on the date this complaint was filed?" instead of "what does the
dict say right now?". Adding/retiring a jurisdiction is a data change
(call `add_jurisdiction_change`), never a code change.

This is intentionally still simple (a Python list, not a GIS database) --
the point for the hackathon demo is to prove the CONCEPT of versioned,
data-driven jurisdiction that survives a real boundary change, not to ship
production-grade GIS. That upgrade path is documented in the decision log.
"""

from datetime import datetime, date
from typing import Optional


def _d(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


# Each record: which area, which authority governed it, and the date range
# that authority was actually in force. `valid_to=None` means "still in
# force today". This list is seed/demo data -- swap for verified MCC
# records before any real deployment.
JURISDICTION_HISTORY = [
    # --- long-standing City Corporation wards (unaffected by the merger) ---
    {"area": "vijayanagar", "authority": "Mysuru City Corporation", "valid_from": _d("2000-01-01"), "valid_to": None},
    {"area": "kuvempunagar", "authority": "Mysuru City Corporation", "valid_from": _d("2000-01-01"), "valid_to": None},
    {"area": "hebbal", "authority": "Mysuru City Corporation", "valid_from": _d("2000-01-01"), "valid_to": None},
    {"area": "saraswathipuram", "authority": "Mysuru City Corporation", "valid_from": _d("2000-01-01"), "valid_to": None},
    {"area": "jayalakshmipuram", "authority": "Mysuru City Corporation", "valid_from": _d("2000-01-01"), "valid_to": None},

    # --- Hootagalli: a Town Panchayat being absorbed into the Corporation ---
    # BEFORE the merger date, it belonged to its own Town Panchayat.
    {"area": "hootagalli", "authority": "Hootagalli Town Panchayat", "valid_from": _d("2000-01-01"), "valid_to": _d("2026-04-01")},
    # FROM the merger date onward, the exact same area belongs to the Corporation.
    {"area": "hootagalli", "authority": "Mysuru City Corporation (newly absorbed)", "valid_from": _d("2026-04-01"), "valid_to": None},

    # --- Bannur Road / Hunsur Road: still pending absorption (not yet merged) ---
    {"area": "bannur road", "authority": "Bannur Road Gram Panchayat", "valid_from": _d("2000-01-01"), "valid_to": None},
    {"area": "hunsur road", "authority": "Hunsur Road Gram Panchayat", "valid_from": _d("2000-01-01"), "valid_to": None},

    # --- Nanjangud: separate local body, not part of this merger at all ---
    {"area": "nanjangud", "authority": "Nanjangud City Municipal Council", "valid_from": _d("2000-01-01"), "valid_to": None},
]


def normalize(value: str) -> str:
    return " ".join((value or "").lower().strip().split())


def add_jurisdiction_change(area: str, new_authority: str, effective_from: date):
    """
    Call this the moment a real boundary change is announced/finalized.
    It retires the area's currently-open record and opens a new one --
    NO code change, NO redeploy needed. This is the function you'd wire to
    an admin-only API endpoint (see main.py) so MCC staff, not developers,
    can keep the system current as more panchayats get absorbed.
    """
    area_normalized = normalize(area)

    for record in JURISDICTION_HISTORY:
        if record["area"] == area_normalized and record["valid_to"] is None:
            record["valid_to"] = effective_from

    JURISDICTION_HISTORY.append({
        "area": area_normalized,
        "authority": new_authority,
        "valid_from": effective_from,
        "valid_to": None,
    })


def _lookup_authority(area_normalized: str, as_of: date):
    """
    Returns (authority, match_quality) where match_quality is one of:
      "matched"       -- exactly one historical record covers this date
      "ambiguous"     -- 2+ overlapping records cover this date (a genuine,
                          unresolved boundary dispute -- do not silently guess)
      "unknown_area"  -- no record exists for this area at all
    """
    matches = [
        r for r in JURISDICTION_HISTORY
        if r["area"] == area_normalized
        and r["valid_from"] <= as_of
        and (r["valid_to"] is None or as_of < r["valid_to"])
    ]

    if len(matches) == 1:
        return matches[0]["authority"], "matched"
    if len(matches) > 1:
        return None, "ambiguous"
    return None, "unknown_area"


def determine_jurisdiction(
    area: str,
    issue_type: str = "",
    reported_at: Optional[datetime] = None,
) -> dict:
    area_normalized = normalize(area)
    issue_normalized = normalize(issue_type)

    current_time = reported_at or datetime.now()
    as_of = current_time.date()

    authority, match_quality = _lookup_authority(area_normalized, as_of)

    if match_quality == "unknown_area":
        # THIS IS THE KEY BEHAVIOUR CHANGE FROM v1.
        # v1 silently fell back to "Relevant Local Civic Authority" -- i.e.
        # it guessed. The brief explicitly warns against a system that
        # "assumes jurisdiction is always obvious." We now say so honestly
        # and route to human review instead of guessing.
        authority = "UNASSIGNED -- needs manual jurisdiction review"
        matched_area = area.title() if area else "Unknown"
    elif match_quality == "ambiguous":
        authority = "DISPUTED -- multiple overlapping jurisdiction records, needs manual review"
        matched_area = area.title()
    else:
        matched_area = area.title()

    # Time-of-day component, unchanged from v1.
    hour = current_time.hour
    routing_mode = "Standard" if 8 <= hour < 20 else "After-hours review"

    safety_terms = ("public safety", "danger", "hazard", "accident", "fallen", "exposed wire")
    if any(term in issue_normalized for term in safety_terms):
        routing_mode = "Priority human review"

    if match_quality in ("unknown_area", "ambiguous"):
        routing_mode = "Priority human review"

    return {
        "authority": authority,
        "jurisdiction": matched_area,
        "routing_mode": routing_mode,
        "match_quality": match_quality,
    }
