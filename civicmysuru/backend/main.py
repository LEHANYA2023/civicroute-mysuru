from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Complaint
from jurisdiction_engine import determine_jurisdiction, add_jurisdiction_change, JURISDICTION_HISTORY
from routing_engine import build_route
from issue_classifier import classify_issue


# Create database tables on startup/import.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CivicMysuru API",
    description="Backend API for citizen complaint routing and tracking.",
    version="1.0.0",
)

# Development-friendly CORS. Restrict this to your deployed frontend domain later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ComplaintCreate(BaseModel):
    citizen_name: str = Field(..., min_length=2, max_length=100)
    area: str = Field(..., min_length=2, max_length=120)
    issue_type: str = Field(..., min_length=2, max_length=80)
    location: Optional[str] = Field(default=None, max_length=300)
    description: str = Field(..., min_length=5, max_length=2000)
    image_name: Optional[str] = Field(default=None, max_length=255)


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(Open|In Progress|Resolved)$")


class IssueClassificationRequest(BaseModel):
    filename: Optional[str] = None
    description: Optional[str] = None


class JurisdictionChangeRequest(BaseModel):
    area: str = Field(..., min_length=2, max_length=120)
    new_authority: str = Field(..., min_length=2, max_length=150)
    effective_from: date


def generate_complaint_id(db: Session) -> str:
    """Generate an ID such as MYR-2026-00001."""
    year = datetime.now().year
    prefix = f"MYR-{year}-"
    last = (
        db.query(Complaint)
        .filter(Complaint.id.like(f"{prefix}%"))
        .order_by(Complaint.id.desc())
        .first()
    )

    next_number = 1
    if last:
        try:
            next_number = int(last.id.split("-")[-1]) + 1
        except (ValueError, IndexError):
            next_number = db.query(Complaint).count() + 1

    return f"{prefix}{next_number:05d}"


@app.get("/")
def root():
    return {
        "name": "CivicMysuru API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "CivicMysuru backend",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/complaints")
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    route = build_route(
        area=payload.area,
        issue_type=payload.issue_type,
        description=payload.description,
        image_name=payload.image_name,
        reported_at=datetime.now(),
    )

    complaint = Complaint(
        id=generate_complaint_id(db),
        citizen_name=payload.citizen_name.strip(),
        area=payload.area.strip(),
        issue_type=route["issue_type"],
        location=(payload.location or "").strip(),
        description=payload.description.strip(),
        authority=route["authority"],
        department=route["department"],
        jurisdiction=route["jurisdiction"],
        routing_reason=route["routing_reason"],
        routing_mode=route["routing_mode"],
        jurisdiction_match_quality=route["jurisdiction_match_quality"],
        priority=route["priority"],
        priority_score=route["priority_score"],
        verification_score=route["verification_score"],
        verification_status=route["verification_status"],
        duplicate=route["duplicate"],
        reused_evidence_flag=route["reused_evidence"]["flag"],
        reused_evidence_reason=route["reused_evidence"]["reason"],
        status="Open",
        image_name=payload.image_name,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint_to_dict(complaint)


@app.get("/api/complaints")
def list_complaints(
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)

    if status:
        query = query.filter(Complaint.status == status)

    if priority:
        query = query.filter(Complaint.priority == priority)

    complaints = query.order_by(Complaint.created_at.desc()).all()

    if search:
        term = search.lower().strip()
        complaints = [
            c for c in complaints
            if term in (c.id or "").lower()
            or term in (c.area or "").lower()
            or term in (c.issue_type or "").lower()
            or term in (c.description or "").lower()
            or term in (c.department or "").lower()
        ]

    return [complaint_to_dict(c) for c in complaints]


@app.get("/api/complaints/{complaint_id}")
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint_to_dict(complaint)


@app.patch("/api/complaints/{complaint_id}/status")
def update_status(
    complaint_id: str,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = payload.status
    complaint.updated_at = datetime.now()

    db.commit()
    db.refresh(complaint)

    return complaint_to_dict(complaint)


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()

    return {
        "total": len(complaints),
        "open": sum(c.status == "Open" for c in complaints),
        "in_progress": sum(c.status == "In Progress" for c in complaints),
        "resolved": sum(c.status == "Resolved" for c in complaints),
        "critical": sum(c.priority == "Critical" for c in complaints),
        "high": sum(c.priority == "High" for c in complaints),
        "medium": sum(c.priority == "Medium" for c in complaints),
        "low": sum(c.priority == "Low" for c in complaints),
    }


@app.get("/api/route-preview")
def route_preview(
    area: str,
    issue_type: str,
    description: str = "",
):
    return build_route(
        area=area,
        issue_type=issue_type,
        description=description,
        image_name=None,
        reported_at=datetime.now(),
        check_duplicate=False,
    )


@app.post("/api/classify-issue")
def classify_issue_api(payload: IssueClassificationRequest):
    result = classify_issue(
        filename=payload.filename or "",
        description=payload.description or "",
    )
    return result


@app.get("/api/jurisdictions")
def list_jurisdiction_history():
    """
    Exposes the full versioned jurisdiction table -- this is what you show
    in your demo video to prove routing is data-driven, not hardcoded.
    """
    return [
        {**record, "valid_from": record["valid_from"].isoformat(),
         "valid_to": record["valid_to"].isoformat() if record["valid_to"] else None}
        for record in JURISDICTION_HISTORY
    ]


@app.post("/api/admin/jurisdiction-change")
def make_jurisdiction_change(payload: JurisdictionChangeRequest):
    """
    THIS IS THE LIVE DEMO OF "THE TWIST".
    Call this once to simulate Mysuru City Corporation officially absorbing
    a panchayat -- no code change, no redeploy. Then submit a complaint for
    that same area dated before vs. after `effective_from` and show the
    routing engine returning a different authority for each, automatically.
    """
    add_jurisdiction_change(
        area=payload.area,
        new_authority=payload.new_authority,
        effective_from=payload.effective_from,
    )
    return {
        "message": f"'{payload.area}' will route to '{payload.new_authority}' "
                   f"from {payload.effective_from.isoformat()} onward. No redeploy needed.",
    }


def complaint_to_dict(c: Complaint):
    return {
        "id": c.id,
        "citizen_name": c.citizen_name,
        "area": c.area,
        "issue_type": c.issue_type,
        "location": c.location,
        "description": c.description,
        "authority": c.authority,
        "department": c.department,
        "jurisdiction": c.jurisdiction,
        "routing_reason": c.routing_reason,
        "routing_mode": c.routing_mode,
        "jurisdiction_match_quality": c.jurisdiction_match_quality,
        "priority": c.priority,
        "priority_score": c.priority_score,
        "verification_score": c.verification_score,
        "verification_status": c.verification_status,
        "duplicate": c.duplicate,
        "reused_evidence_flag": c.reused_evidence_flag,
        "reused_evidence_reason": c.reused_evidence_reason,
        "status": c.status,
        "image_name": c.image_name,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


if __name__ == "__main__":
    import uvicorn

    # Lets the whole backend start with just: python main.py
    # (equivalent to running: uvicorn main:app --reload --host 127.0.0.1 --port 8000)
    print("Starting CivicMysuru backend on http://127.0.0.1:8000")
    print("Interactive API docs: http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

