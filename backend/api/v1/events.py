"""
events.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Fan Event resources.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, g
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from psycopg2.extras import RealDictCursor

from database import SessionLocal, get_db as get_raw_db_conn
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
    List all upcoming fan events safely.
    """
    try:
        # The v_event_feed view does not contain a sport_name column. 
        # We query all upcoming events without filtering by sport to prevent 500 errors.
        query = "SELECT * FROM v_event_feed WHERE event_status != 'past' ORDER BY event_date ASC"

        with get_raw_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                results = cur.fetchall()
                data = [dict(row) for row in results]
                
                return jsonify({"data": data}), 200

    except Exception as e:
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500

@events_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id: int):
    """
    GET /api/v1/events/<id>
    ───────────────────────
    Single event detail from v_event_feed view.
    """
    try:
        with get_raw_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM v_event_feed WHERE event_id = %s
                """, (event_id,))
                
                result = cur.fetchone()
                
                if result is None:
                    return jsonify(ErrorOut(error=f"Event {event_id} not found", code="NOT_FOUND").model_dump()), 404

                return jsonify(dict(result)), 200

    except Exception as e:
        return jsonify(
            ErrorOut(error=str(e), code="DB_ERROR").model_dump()
        ), 500


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@events_bp.route("/admin/events", methods=["POST"])
@require_auth
@require_role(["admin", "team_manager"])
def create_event():
    """
    POST /api/v1/admin/events
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

    except Exception as e:
        db.rollback()
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
    finally:
        db.close()


@events_bp.route("/admin/events/<int:event_id>", methods=["PUT"])
@require_auth
@require_role(["admin", "team_manager"])
def update_event(event_id: int):
    """
    PUT /api/v1/admin/events/<id>
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

    except Exception as e:
        db.rollback()
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
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
    """
    db = get_db()
    try:
        user_id = g.user.get("sub")

        event = db.query(FanEvent).filter(FanEvent.event_id == event_id).first()
        if event is None:
            return jsonify(ErrorOut(error=f"Event {event_id} not found", code="NOT_FOUND").model_dump()), 404

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

        registered = (
            db.query(func.count(EventRegistration.registration_id))
            .filter(EventRegistration.event_id == event_id)
            .scalar()
        ) or 0

        if registered >= event.capacity:
            return jsonify(
                ErrorOut(error="This event is fully booked.", code="EVENT_FULL").model_dump()
            ), 409

        reg = EventRegistration(
            event_id      = event_id,
            user_id       = user_id,
            registered_at = datetime.now(tz=timezone.utc),
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)

        return jsonify(EventRegistrationOut.model_validate(reg).model_dump(mode="json")), 201

    except Exception as e:
        db.rollback()
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
    finally:
        db.close()


@events_bp.route("/events/<int:event_id>/register", methods=["DELETE"])
@require_auth
def cancel_registration(event_id: int):
    """
    DELETE /api/v1/events/<id>/register
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

    except Exception as e:
        db.rollback()
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
    finally:
        db.close()