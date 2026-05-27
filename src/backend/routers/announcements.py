"""
Announcement endpoints for the High School Management System API.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Payload used to create or update announcements."""

    title: str = Field(..., min_length=3, max_length=80)
    message: str = Field(..., min_length=10, max_length=280)
    start_date: Optional[str] = None
    expiration_date: str


def parse_iso_date(value: Optional[str], field_name: str) -> Optional[date]:
    """Parse and validate ISO dates in YYYY-MM-DD format."""
    if value in (None, ""):
        return None

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must use the YYYY-MM-DD format"
        ) from exc


def get_authenticated_teacher(teacher_username: Optional[str]) -> Dict[str, Any]:
    """Validate teacher identity for announcement management actions."""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def serialize_announcement(announcement: Dict[str, Any], *, today: Optional[date] = None) -> Dict[str, Any]:
    """Convert a MongoDB announcement document into a JSON-safe payload."""
    today = today or date.today()
    start_date = parse_iso_date(announcement.get("start_date"), "start_date")
    expiration_date = parse_iso_date(
        announcement.get("expiration_date"),
        "expiration_date"
    )

    is_active = bool(expiration_date and expiration_date >= today)
    if start_date:
        is_active = is_active and start_date <= today

    return {
        "id": announcement.get("id") or announcement.get("_id"),
        "title": announcement["title"],
        "message": announcement["message"],
        "start_date": announcement.get("start_date"),
        "expiration_date": announcement["expiration_date"],
        "created_by": announcement.get("created_by"),
        "is_active": is_active,
    }


def validate_payload(payload: AnnouncementPayload) -> AnnouncementPayload:
    """Apply business rules for announcement dates."""
    start_date = parse_iso_date(payload.start_date, "start_date")
    expiration_date = parse_iso_date(payload.expiration_date, "expiration_date")

    if expiration_date is None:
        raise HTTPException(status_code=400, detail="expiration_date is required")

    if start_date and start_date > expiration_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after expiration_date"
        )

    return payload


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_active_announcements() -> List[Dict[str, Any]]:
    """Return currently active announcements for the public site header."""
    today = date.today()
    announcements = [
        serialize_announcement(announcement, today=today)
        for announcement in announcements_collection.find().sort("expiration_date", 1)
    ]
    return [announcement for announcement in announcements if announcement["is_active"]]


@router.get("/manage", response_model=List[Dict[str, Any]])
def list_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Return all announcements for authenticated management screens."""
    get_authenticated_teacher(teacher_username)
    return [
        serialize_announcement(announcement)
        for announcement in announcements_collection.find().sort("expiration_date", 1)
    ]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload = Body(...),
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Create a new announcement. Requires an authenticated teacher."""
    teacher = get_authenticated_teacher(teacher_username)
    validated_payload = validate_payload(payload)

    next_id = f"announcement-{uuid4().hex}"
    announcement = {
        "id": next_id,
        "title": validated_payload.title.strip(),
        "message": validated_payload.message.strip(),
        "start_date": validated_payload.start_date,
        "expiration_date": validated_payload.expiration_date,
        "created_by": teacher["username"],
    }
    announcements_collection.insert_one({"_id": next_id, **announcement})
    return serialize_announcement(announcement)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload = Body(...),
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement. Requires an authenticated teacher."""
    get_authenticated_teacher(teacher_username)
    validated_payload = validate_payload(payload)

    result = announcements_collection.update_one(
        {"_id": announcement_id},
        {
            "$set": {
                "title": validated_payload.title.strip(),
                "message": validated_payload.message.strip(),
                "start_date": validated_payload.start_date,
                "expiration_date": validated_payload.expiration_date,
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated_announcement = announcements_collection.find_one({"_id": announcement_id})
    return serialize_announcement(updated_announcement)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """Delete an announcement. Requires an authenticated teacher."""
    get_authenticated_teacher(teacher_username)
    result = announcements_collection.delete_one({"_id": announcement_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}
