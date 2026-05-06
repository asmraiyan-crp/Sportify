"""
sports.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Sport resources.

Public endpoints:
    GET  /api/v1/sports          – list all sports
    GET  /api/v1/sports/<id>     – single sport detail

Admin-only endpoints:
    POST   /api/v1/admin/sports          – create a sport
    PUT    /api/v1/admin/sports/<id>     – edit a sport
    DELETE /api/v1/admin/sports/<id>     – delete a sport

Registration in app.py  (add these lines):
    from api.v1.sports import sports_bp, admin_sports_bp
    app.register_blueprint(sports_bp,       url_prefix="/api/v1")
    app.register_blueprint(admin_sports_bp, url_prefix="/api/v1/admin")
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from functools import wraps
from uuid import UUID

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from model.model import Sport
from model.schemas import (
    ErrorOut,
    MessageOut,
    PaginationMeta,
    SportCreate,
    SportOut,
    SportUpdate,
)


# ══════════════════════════════════════════════════════════════════════════════
# Blueprints
# Two blueprints keep the url_prefix clean:
#   sports_bp       → registered at /api/v1        (public  routes /sports/…)
#   admin_sports_bp → registered at /api/v1/admin  (admin   routes /sports/…)
# ══════════════════════════════════════════════════════════════════════════════

sports_bp       = Blueprint("sports",       __name__)
admin_sports_bp = Blueprint("admin_sports", __name__)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers  (identical pattern to the working follow.py)
# ══════════════════════════════════════════════════════════════════════════════

def get_db():
    """Return a SQLAlchemy session."""
    return SessionLocal()


def require_auth(f):
    """
    Reads  Authorization: Bearer <token>  from the request header.
    Sets   g.current_user_id  (str UUID) for downstream use.

    For testing:  pass a real UUID from your profiles table as the token.
    For production: replace the try/except block with your real JWT decode.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify(
                ErrorOut(
                    error="Authorization header missing or malformed",
                    code="UNAUTHORIZED",
                ).model_dump()
            ), 401

        token = auth_header.removeprefix("Bearer ").strip()

        # ── Swap this block with your real JWT decode when auth is ready ──────
        try:
            UUID(token)                   # confirm it is a valid UUID
            g.current_user_id = token     # treat the token as the user UUID
        except ValueError:
            return jsonify(
                ErrorOut(error="Invalid token", code="UNAUTHORIZED").model_dump()
            ), 401
        # ─────────────────────────────────────────────────────────────────────

        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """
    Must be stacked BELOW @require_auth so g.current_user_id is already set.

    Checks the role column in the profiles table for the current user.
    Returns 403 if the user is not an admin.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        db = get_db()
        try:
            from model.model import Profile          # local import avoids circular
            user = db.query(Profile).filter(
                Profile.id == UUID(g.current_user_id)
            ).first()

            if user is None or user.role != "admin":
                return jsonify(
                    ErrorOut(error="Forbidden — admin only", code="NOT_ADMIN").model_dump()
                ), 403
        finally:
            db.close()

        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES  (no auth required)
# ══════════════════════════════════════════════════════════════════════════════

@sports_bp.route("/sports", methods=["GET"])
def list_sports():
    """
    GET /api/v1/sports
    ──────────────────
    Returns all sports.  Supports optional pagination:

        ?page=<int>   – page number  (default 1)
        ?limit=<int>  – per page     (default 20, max 100)

    Response 200:
        {
          "data": [ SportOut, … ],
          "meta": PaginationMeta
        }
    """
    db = get_db()
    try:
        # ── parse query params ────────────────────────────────────────────────
        try:
            page  = max(1,   int(request.args.get("page",  1)))
            limit = min(100, max(1, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            return jsonify(
                ErrorOut(error="Invalid query parameter", code="BAD_QUERY").model_dump()
            ), 400

        # ── query ─────────────────────────────────────────────────────────────
        q      = db.query(Sport).order_by(Sport.name)
        total  = q.count()
        sports = q.offset((page - 1) * limit).limit(limit).all()

        # ── serialise ─────────────────────────────────────────────────────────
        data = [SportOut.model_validate(s).model_dump(mode="json") for s in sports]

        total_pages = max(1, (total + limit - 1) // limit)
        meta = PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ).model_dump()

        return jsonify({"data": data, "meta": meta}), 200

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@sports_bp.route("/sports/<int:sport_id>", methods=["GET"])
def get_sport(sport_id: int):
    """
    GET /api/v1/sports/<id>
    ───────────────────────
    Returns a single sport by primary key.

    Response 200: SportOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        sport = db.query(Sport).filter(Sport.sport_id == sport_id).first()

        if sport is None:
            return jsonify(
                ErrorOut(
                    error=f"Sport {sport_id} not found",
                    code="NOT_FOUND",
                ).model_dump()
            ), 404

        return jsonify(SportOut.model_validate(sport).model_dump(mode="json")), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES  (role == 'admin' required)
# ══════════════════════════════════════════════════════════════════════════════

@admin_sports_bp.route("/sports", methods=["POST"])
@require_auth
@require_admin
def create_sport():
    """
    POST /api/v1/admin/sports
    ─────────────────────────
    Create a new sport.

    Request body (JSON): SportCreate
        { "name": "Football", "description": "The beautiful game." }

    Response 201: SportOut
    Response 400: ErrorOut  (validation error)
    Response 409: ErrorOut  (name already exists)
    """
    db = get_db()
    try:
        # ── validate body ─────────────────────────────────────────────────────
        try:
            payload = SportCreate.model_validate(
                request.get_json(force=True) or {}
            )
        except ValidationError as exc:
            return jsonify(
                ErrorOut(
                    error="Validation error",
                    code="VALIDATION_ERROR",
                    details=exc.errors(),
                ).model_dump()
            ), 400

        # ── uniqueness check ──────────────────────────────────────────────────
        existing = (
            db.query(Sport).filter(Sport.name == payload.name).first()
        )
        if existing:
            return jsonify(
                ErrorOut(
                    error=f"Sport '{payload.name}' already exists.",
                    code="DUPLICATE_SPORT",
                ).model_dump()
            ), 409

        # ── insert ────────────────────────────────────────────────────────────
        sport = Sport(
            name        = payload.name,
            description = payload.description,
        )
        db.add(sport)
        db.commit()
        db.refresh(sport)

        return jsonify(SportOut.model_validate(sport).model_dump(mode="json")), 201

    except IntegrityError:
        db.rollback()
        return jsonify(
            ErrorOut(
                error="Sport name must be unique.",
                code="DUPLICATE_SPORT",
            ).model_dump()
        ), 409

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@admin_sports_bp.route("/sports/<int:sport_id>", methods=["PUT"])
@require_auth
@require_admin
def update_sport(sport_id: int):
    """
    PUT /api/v1/admin/sports/<id>
    ─────────────────────────────
    Edit a sport's name or description.  Only supplied fields are updated.

    Request body (JSON): SportUpdate  (all fields optional)
        { "name": "Soccer", "description": "Updated description." }

    Response 200: SportOut
    Response 400: ErrorOut  (validation error)
    Response 404: ErrorOut  (sport not found)
    Response 409: ErrorOut  (name already taken by another sport)
    """
    db = get_db()
    try:
        # ── fetch ─────────────────────────────────────────────────────────────
        sport = db.query(Sport).filter(Sport.sport_id == sport_id).first()
        if sport is None:
            return jsonify(
                ErrorOut(
                    error=f"Sport {sport_id} not found",
                    code="NOT_FOUND",
                ).model_dump()
            ), 404

        # ── validate body ─────────────────────────────────────────────────────
        try:
            payload = SportUpdate.model_validate(
                request.get_json(force=True) or {}
            )
        except ValidationError as exc:
            return jsonify(
                ErrorOut(
                    error="Validation error",
                    code="VALIDATION_ERROR",
                    details=exc.errors(),
                ).model_dump()
            ), 400

        # ── uniqueness check (exclude self) ───────────────────────────────────
        if payload.name is not None and payload.name != sport.name:
            duplicate = (
                db.query(Sport)
                .filter(
                    Sport.name     == payload.name,
                    Sport.sport_id != sport_id,
                )
                .first()
            )
            if duplicate:
                return jsonify(
                    ErrorOut(
                        error=f"Sport '{payload.name}' already exists.",
                        code="DUPLICATE_SPORT",
                    ).model_dump()
                ), 409

        # ── apply updates ─────────────────────────────────────────────────────
        if payload.name        is not None: sport.name        = payload.name
        if payload.description is not None: sport.description = payload.description

        db.commit()
        db.refresh(sport)

        return jsonify(SportOut.model_validate(sport).model_dump(mode="json")), 200

    except IntegrityError:
        db.rollback()
        return jsonify(
            ErrorOut(
                error="Sport name must be unique.",
                code="DUPLICATE_SPORT",
            ).model_dump()
        ), 409

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@admin_sports_bp.route("/sports/<int:sport_id>", methods=["DELETE"])
@require_auth
@require_admin
def delete_sport(sport_id: int):
    """
    DELETE /api/v1/admin/sports/<id>
    ────────────────────────────────
    Delete a sport.

    ⚠  The Sport model has  ondelete='RESTRICT'  on the league, team, and
    player foreign keys — meaning the DB will block deletion if any league,
    team, or player still references this sport.  The route catches that and
    returns a clear 409 instead of a raw 500.

    Response 200: MessageOut
    Response 404: ErrorOut  (sport not found)
    Response 409: ErrorOut  (sport still referenced by leagues / teams / players)
    """
    db = get_db()
    try:
        sport = db.query(Sport).filter(Sport.sport_id == sport_id).first()
        if sport is None:
            return jsonify(
                ErrorOut(
                    error=f"Sport {sport_id} not found",
                    code="NOT_FOUND",
                ).model_dump()
            ), 404

        db.delete(sport)
        db.commit()

        return jsonify(
            MessageOut(message=f"Sport '{sport.name}' deleted successfully.").model_dump()
        ), 200

    except IntegrityError:
        db.rollback()
        return jsonify(
            ErrorOut(
                error=(
                    "Cannot delete this sport because leagues, teams, or players "
                    "still reference it. Remove those records first."
                ),
                code="SPORT_IN_USE",
            ).model_dump()
        ), 409

    finally:
        db.close()