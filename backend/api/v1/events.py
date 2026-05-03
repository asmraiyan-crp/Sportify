"""
events.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Fan Event resources.

Registered with the app under prefix /api/v1
so all routes here are relative to that.

Public endpoints:
    GET  /events                    – list upcoming events ordered by event_date
    GET  /events/<id>               – single event detail with registration count

Admin-only endpoints:
    POST /admin/events              – create a new event
    PUT  /admin/events/<id>         – edit event details

Authenticated endpoints:
    POST   /events/<id>/register    – register for an event (rejects if full)
    DELETE /events/<id>/register    – cancel own registration
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import SessionLocal
from model.model import FanEvent, EventRegistration, Profile
from model.schemas import (
    FanEventOut,
    FanEventCreate,
    FanEventUpdate,
    EventRegistrationOut,
    PaginationMeta,
    ErrorOut,
    MessageOut,
)
from core.auth import require_auth, require_role

events_bp = Blueprint("events", __name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_db():
    return SessionLocal()


def _event_out(event: FanEvent, db) -> dict:
    """Serialize a FanEvent ORM object, injecting computed registration counts."""
    registered = (
        db.query(func.count(EventRegistration.registration_id))
        .filter(EventRegistration.event_id == event.event_id)
        .scalar()
    ) or 0

    data = FanEventOut.model_validate(event).model_dump(mode="json")
    data["registered"] = registered
    data["spots_left"] = max(0, event.capacity - registered)
    return data


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@events_bp.route("/events", methods=["GET"])
def list_events():
    """
    GET /api/v1/events
    ──────────────────
    List all upcoming fan events (event_date >= now), ordered by event_date ASC.

    Query params:
        ?page=<int>   – page number (default 1)
        ?limit=<int>  – results per page (default 20, max 100)

    Response 200:
        { "data": [ FanEventOut, … ], "meta": PaginationMeta }
    """
    db = get_db()
    try:
        try:
            page  = max(1, int(request.args.get("page",  1)))
            limit = min(100, max(1, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            return jsonify(ErrorOut(error="Invalid query parameter", code="BAD_QUERY").model_dump()), 400

        now = datetime.now(tz=timezone.utc)

        q = (
            db.query(FanEvent)
            .filter(FanEvent.event_date >= now)
            .order_by(FanEvent.event_date.asc())
        )

        total  = q.count()
        events = q.offset((page - 1) * limit).limit(limit).all()

        data        = [_event_out(e, db) for e in events]
        total_pages = max(1, (total + limit - 1) // limit)
        meta        = PaginationMeta(
            page=page, limit=limit, total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ).model_dump()

        return jsonify({"data": data, "meta": meta}), 200
    finally:
        db.close()


@events_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id: int):
    """
    GET /api/v1/events/<id>
    ───────────────────────
    Single event detail including capacity and current registration count.

    Response 200: FanEventOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        event = db.query(FanEvent).filter(FanEvent.event_id == event_id).first()

        if event is None:
            return jsonify(ErrorOut(error=f"Event {event_id} not found", code="NOT_FOUND").model_dump()), 404

        return jsonify(_event_out(event, db)), 200
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@events_bp.route("/admin/events", methods=["POST"])
@require_auth
@require_role(["admin"])
def create_event():
    """
    POST /api/v1/admin/events
    ─────────────────────────
    Admin creates a new fan event.

    Request body (JSON): FanEventCreate
        {
          "title":       "Watch Party – UCL Final",
          "description": "Join us at the fan zone!",
          "event_date":  "2026-06-01T18:00:00Z",
          "location":    "Dhaka Fan Zone",
          "capacity":    200
        }

    Response 201: FanEventOut
    Response 400: ErrorOut (validation)
    """
    db = get_db()
    try:
        try:
            payload = FanEventCreate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
    ErrorOut(error="Validation error", code="VALIDATION_ERROR",
             details={"errors": exc.errors()}).model_dump()
), 400

        admin_id = g.user.get("sub")

        event = FanEvent(
            title       = payload.title,
            description = payload.description,
            event_date  = payload.event_date,
            location    = payload.location,
            capacity    = payload.capacity,
            created_by  = admin_id,
            created_at  = datetime.now(tz=timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        return jsonify(_event_out(event, db)), 201
    finally:
        db.close()


@events_bp.route("/admin/events/<int:event_id>", methods=["PUT"])
@require_auth
@require_role(["admin"])
def update_event(event_id: int):
    """
    PUT /api/v1/admin/events/<id>
    ─────────────────────────────
    Admin edits event details. All fields are optional (partial update).

    Request body (JSON): FanEventUpdate
        {
          "title":    "New Title",
          "capacity": 300
        }

    Response 200: FanEventOut
    Response 400: ErrorOut (validation)
    Response 404: ErrorOut (not found)
    """
    db = get_db()
    try:
        event = db.query(FanEvent).filter(FanEvent.event_id == event_id).first()

        if event is None:
            return jsonify(ErrorOut(error=f"Event {event_id} not found", code="NOT_FOUND").model_dump()), 404

        try:
            payload = FanEventUpdate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
    ErrorOut(error="Validation error", code="VALIDATION_ERROR",
             details={"errors": exc.errors()}).model_dump()
), 400

        # Guard: don't let capacity drop below current registration count
        if payload.capacity is not None:
            registered = (
                db.query(func.count(EventRegistration.registration_id))
                .filter(EventRegistration.event_id == event_id)
                .scalar()
            ) or 0
            if payload.capacity < registered:
                return jsonify(
                    ErrorOut(
                        error=f"Cannot set capacity below current registrations ({registered}).",
                        code="CAPACITY_TOO_LOW",
                    ).model_dump()
                ), 409

        if payload.title       is not None: event.title       = payload.title
        if payload.description is not None: event.description = payload.description
        if payload.event_date  is not None: event.event_date  = payload.event_date
        if payload.location    is not None: event.location    = payload.location
        if payload.capacity    is not None: event.capacity    = payload.capacity

        db.commit()
        db.refresh(event)

        return jsonify(_event_out(event, db)), 200
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES  (any logged-in user)
# ══════════════════════════════════════════════════════════════════════════════

@events_bp.route("/events/<int:event_id>/register", methods=["POST"])
@require_auth
def register_for_event(event_id: int):
    """
    POST /api/v1/events/<id>/register
    ──────────────────────────────────
    Register the authenticated user for a fan event.

    Rejects with 409 if:
      • User is already registered
      • Event is at full capacity

    Response 201: EventRegistrationOut
    Response 404: ErrorOut (event not found)
    Response 409: ErrorOut (already registered / full)
    """
    db = get_db()
    try:
        user_id = g.user.get("sub")

        event = db.query(FanEvent).filter(FanEvent.event_id == event_id).first()
        if event is None:
            return jsonify(ErrorOut(error=f"Event {event_id} not found", code="NOT_FOUND").model_dump()), 404

        # Already registered?
        existing = (
            db.query(EventRegistration)
            .filter(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id  == user_id,
            )
            .first()
        )
        if existing:
            return jsonify(
                ErrorOut(error="You are already registered for this event.", code="ALREADY_REGISTERED").model_dump()
            ), 409

        # Capacity check
        registered = (
            db.query(func.count(EventRegistration.registration_id))
            .filter(EventRegistration.event_id == event_id)
            .scalar()
        ) or 0

        if registered >= event.capacity:
            return jsonify(
                ErrorOut(error="This event is fully booked.", code="EVENT_FULL").model_dump()
            ), 409

        # Create registration
        reg = EventRegistration(
            event_id      = event_id,
            user_id       = user_id,
            registered_at = datetime.now(tz=timezone.utc),
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)

        return jsonify(EventRegistrationOut.model_validate(reg).model_dump(mode="json")), 201
    finally:
        db.close()


@events_bp.route("/events/<int:event_id>/register", methods=["DELETE"])
@require_auth
def cancel_registration(event_id: int):
    """
    DELETE /api/v1/events/<id>/register
    ────────────────────────────────────
    Cancel the authenticated user's own registration.

    Response 200: MessageOut
    Response 404: ErrorOut (event not found, or not registered)
    """
    db = get_db()
    try:
        user_id = g.user.get("sub")

        event = db.query(FanEvent).filter(FanEvent.event_id == event_id).first()
        if event is None:
            return jsonify(ErrorOut(error=f"Event {event_id} not found", code="NOT_FOUND").model_dump()), 404

        reg = (
            db.query(EventRegistration)
            .filter(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id  == user_id,
            )
            .first()
        )
        if reg is None:
            return jsonify(
                ErrorOut(error="You are not registered for this event.", code="NOT_REGISTERED").model_dump()
            ), 404

        db.delete(reg)
        db.commit()

        return jsonify(MessageOut(message="Registration cancelled successfully.").model_dump()), 200
    finally:
        db.close()