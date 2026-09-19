"""
CivicMysuru routing engine.

Combines:
1. Issue -> department mapping
2. Area -> jurisdiction mapping
3. Priority calculation
4. Basic verification scoring
5. Prototype duplicate detection
"""

from datetime import datetime

from database import SessionLocal
from jurisdiction_engine import determine_jurisdiction
from issue_classifier import classify_issue


DEPARTMENT_RULES = {
    "road": "Roads & Infrastructure",
    "pothole": "Roads & Infrastructure",
    "garbage": "Solid Waste Management",
    "waste": "Solid Waste Management",
    "streetlight": "Electrical / Street Lighting",
    "street light": "Electrical / Street Lighting",
    "drainage": "Drainage & Sanitation",
    "drain": "Drainage & Sanitation",
    "water supply": "Water Supply",
    "water": "Water Supply",
    "public safety": "Public Safety / Civic Enforcement",
    "safety": "Public Safety / Civic Enforcement",
}


CRITICAL_TERMS = {
    "accident",
    "danger",
    "hazard",
    "exposed wire",
    "fire",
    "collapse",
    "blocked emergency",
}

HIGH_TERMS = {
    "overflow",
    "flood",
    "sewage",
    "major pothole",
    "open manhole",
    "broken pole",
    "no streetlight",
}


def normalize(value: str) -> str:
    return " ".join((value or "").lower().strip().split())


def department_for_issue(issue_type: str) -> str:
    text = normalize(issue_type)

    for keyword, department in DEPARTMENT_RULES.items():
        if keyword in text:
            return department

    return "General Civic Administration"


def calculate_priority(issue_type: str, description: str):
    text = normalize(f"{issue_type} {description}")

    score = 20

    for term in CRITICAL_TERMS:
        if term in text:
            score += 30

    for term in HIGH_TERMS:
        if term in text:
            score += 18

    if any(x in text for x in ["multiple", "entire road", "whole area", "many people"]):
        score += 10

    if len(description or "") > 250:
        score += 5

    score = min(score, 100)

    if score >= 70:
        label = "Critical"
    elif score >= 50:
        label = "High"
    elif score >= 30:
        label = "Medium"
    else:
        label = "Low"

    return label, score


def verification_score(description: str, image_name: str | None):
    score = 35

    if len(description or "") >= 80:
        score += 20
    elif len(description or "") >= 30:
        score += 10

    if image_name:
        score += 30

    score = min(score, 100)

    if score >= 75:
        status = "Verified Candidate"
    elif score >= 50:
        status = "Moderate Evidence"
    else:
        status = "Needs Review"

    return score, status


def duplicate_check(
    area: str,
    issue_type: str,
    description: str,
) -> bool:
    """
    Lightweight duplicate detector for the hackathon prototype.
    It compares recent complaints in the same area and issue category.
    """
    from models import Complaint

    db = SessionLocal()
    try:
        area_text = normalize(area)
        issue_text = normalize(issue_type)

        candidates = (
            db.query(Complaint)
            .filter(Complaint.area.ilike(f"%{area_text}%"))
            .filter(Complaint.issue_type.ilike(f"%{issue_text}%"))
            .order_by(Complaint.created_at.desc())
            .limit(25)
            .all()
        )

        new_words = {
            w for w in normalize(description).split()
            if len(w) >= 4
        }

        for candidate in candidates:
            old_words = {
                w for w in normalize(candidate.description).split()
                if len(w) >= 4
            }

            overlap = len(new_words.intersection(old_words))

            if overlap >= 4:
                return True

        return False
    finally:
        db.close()


def reused_evidence_check(image_name: str | None) -> dict:
    """
    Fake-evidence heuristic for the hackathon MVP.

    A real deployment would compute a perceptual hash (pHash) of the actual
    uploaded image bytes and compare against every hash seen before -- that
    catches a photo reused across unrelated complaints even if renamed.
    This MVP compares the filename the browser sends, which is a strictly
    weaker signal (renaming defeats it) but proves the exact required demo
    behaviour end-to-end: "if the same piece of evidence shows up on two
    different complaints, flag it instead of trusting both equally."
    The swap to real pHash only touches this function.
    """
    if not image_name:
        return {"flag": False, "reason": None}

    from models import Complaint

    db = SessionLocal()
    try:
        reused = (
            db.query(Complaint)
            .filter(Complaint.image_name == image_name)
            .order_by(Complaint.created_at.asc())
            .first()
        )
        if reused:
            return {
                "flag": True,
                "reason": f"This evidence filename was already used on complaint {reused.id}.",
            }
        return {"flag": False, "reason": None}
    finally:
        db.close()


def build_route(
    area: str,
    issue_type: str,
    description: str,
    image_name: str | None = None,
    reported_at: datetime | None = None,
    check_duplicate: bool = True,
):
    classification = classify_issue(
        filename=image_name or "",
        description=description or "",
    )

    final_issue = issue_type.strip() if issue_type.strip() else classification["issue_type"]

    jurisdiction = determine_jurisdiction(
        area=area,
        issue_type=final_issue,
        reported_at=reported_at,
    )

    department = department_for_issue(final_issue)
    priority, priority_score = calculate_priority(final_issue, description)
    verification, verification_status = verification_score(
        description,
        image_name,
    )

    duplicate = False
    reused_evidence = {"flag": False, "reason": None}
    if check_duplicate:
        duplicate = duplicate_check(area, final_issue, description)
        reused_evidence = reused_evidence_check(image_name)

    # A reused photo is a strong fake-evidence signal -- pull verification
    # down hard rather than averaging it away.
    if reused_evidence["flag"]:
        verification = max(verification - 40, 5)
        verification_status = "Flagged: Possible Fake Evidence"

    reason = (
        f"Area '{area}' matched the prototype jurisdiction "
        f"'{jurisdiction['jurisdiction']}' (match quality: {jurisdiction['match_quality']}). "
        f"Issue '{final_issue}' was mapped to '{department}'. "
        f"Routing mode: {jurisdiction['routing_mode']}."
    )

    return {
        "issue_type": final_issue,
        "authority": jurisdiction["authority"],
        "jurisdiction": jurisdiction["jurisdiction"],
        "jurisdiction_match_quality": jurisdiction["match_quality"],
        "department": department,
        "routing_mode": jurisdiction["routing_mode"],
        "routing_reason": reason,
        "priority": priority,
        "priority_score": priority_score,
        "verification_score": verification,
        "verification_status": verification_status,
        "duplicate": duplicate,
        "reused_evidence": reused_evidence,
        "classifier": classification,
    }

