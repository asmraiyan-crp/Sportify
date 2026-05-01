"""
teams.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Team resources.

Registered with the app under prefix /api/v1
so all routes here are relative to that.

Public endpoints:
    GET  /teams                   – list teams, optional ?sport_id= ?league_id= filters
    GET  /teams/<id>              – single team profile (sport, country, founded_year, home_ground)
    GET  /teams/<id>/squad        – full player list with injury_status

Admin-only endpoints  (require role == 'admin'):
    POST /admin/teams             – create a new team
    PUT  /admin/teams/<id>        – edit team details or upload logo_url
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request, g
from pydantic import ValidationError
from sqlalchemy.orm import joinedload

from database import SessionLocal
from model.model import Team, Sport, Player, TeamLeague
from model.schemas import (
    TeamOut,
    TeamCreate,
    TeamUpdate,
    PlayerOut,
    ErrorOut,
    MessageOut,
    PaginationMeta,
)
from core.auth import require_auth, require_role


# ─── Blueprint ────────────────────────────────────────────────────────────────

teams_bp = Blueprint("teams", __name__)


# ─── DB helper ───────────────────────────────────────────────────────────────

def get_db():
    return SessionLocal()


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@teams_bp.route("/teams", methods=["GET"])
def list_teams():
    """
    GET /api/v1/teams
    ─────────────────
    List all teams. Supports optional query parameters:

        ?sport_id=<int>   – filter by sport
        ?league_id=<int>  – filter by league (via team_league junction)
        ?page=<int>       – page number (default 1)
        ?limit=<int>      – results per page (default 20, max 100)

    Response 200:
        {
          "data": [ TeamOut, … ],
          "meta": PaginationMeta
        }
    """
    db = get_db()
    try:
        # ── parse query params ────────────────────────────────────────────────
        try:
            sport_id  = int(request.args["sport_id"])  if "sport_id"  in request.args else None
            league_id = int(request.args["league_id"]) if "league_id" in request.args else None
            page      = max(1, int(request.args.get("page",  1)))
            limit     = min(100, max(1, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            return jsonify(ErrorOut(error="Invalid query parameter", code="BAD_QUERY").model_dump()), 400

        # ── build query ───────────────────────────────────────────────────────
        q = db.query(Team).options(joinedload(Team.sport))

        if sport_id:
            q = q.filter(Team.sport_id == sport_id)

        if league_id:
            # Filter via the team_league junction table
            q = q.join(TeamLeague, Team.team_id == TeamLeague.team_id)\
                 .filter(TeamLeague.league_id == league_id)

        total = q.count()
        teams = q.order_by(Team.name).offset((page - 1) * limit).limit(limit).all()

        # ── serialise ─────────────────────────────────────────────────────────
        data = [TeamOut.model_validate(t).model_dump(mode="json") for t in teams]

        total_pages = max(1, (total + limit - 1) // limit)
        meta = PaginationMeta(
            page=page, limit=limit, total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ).model_dump()

        return jsonify({"data": data, "meta": meta}), 200

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@teams_bp.route("/teams/<int:team_id>", methods=["GET"])
def get_team(team_id: int):
    """
    GET /api/v1/teams/<id>
    ──────────────────────
    Single team profile including sport, country, founded_year, home_ground.

    Response 200: TeamOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        team = (
            db.query(Team)
            .options(joinedload(Team.sport))
            .filter(Team.team_id == team_id)
            .first()
        )

        if team is None:
            return jsonify(ErrorOut(error=f"Team {team_id} not found", code="NOT_FOUND").model_dump()), 404

        return jsonify(TeamOut.model_validate(team).model_dump(mode="json")), 200

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@teams_bp.route("/teams/<int:team_id>/squad", methods=["GET"])
def get_squad(team_id: int):
    """
    GET /api/v1/teams/<id>/squad
    ────────────────────────────
    Full player list for the team including injury_status.

    Response 200:
        {
          "team_id": 1,
          "team_name": "Arsenal",
          "squad": [ PlayerOut, … ]
        }
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        team = (
            db.query(Team)
            .options(joinedload(Team.sport))
            .filter(Team.team_id == team_id)
            .first()
        )

        if team is None:
            return jsonify(ErrorOut(error=f"Team {team_id} not found", code="NOT_FOUND").model_dump()), 404

        players = (
            db.query(Player)
            .options(
                joinedload(Player.team),
                joinedload(Player.sport),
            )
            .filter(Player.team_id == team_id)
            .order_by(Player.jersey_number.nullslast(), Player.name)
            .all()
        )

        squad = [PlayerOut.model_validate(p).model_dump(mode="json") for p in players]

        return jsonify({
            "team_id":   team.team_id,
            "team_name": team.name,
            "squad":     squad,
        }), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@teams_bp.route("/admin/teams", methods=["POST"])
@require_auth
@require_role(["admin"])
def create_team():
    """
    POST /api/v1/admin/teams
    ────────────────────────
    Admin creates a new team.

    Request body (JSON): TeamCreate
        {
          "sport_id":     1,
          "name":         "Arsenal FC",
          "country":      "England",
          "founded_year": 1886,
          "home_ground":  "Emirates Stadium",
          "logo_url":     "https://example.com/logo.png"   (optional)
        }

    Response 201: TeamOut
    Response 400: ErrorOut  (validation error)
    Response 404: ErrorOut  (sport not found)
    Response 409: ErrorOut  (duplicate team name in same sport)
    """
    db = get_db()
    try:
        # ── validate body ─────────────────────────────────────────────────────
        try:
            payload = TeamCreate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 400

        # ── verify sport exists ───────────────────────────────────────────────
        sport = db.query(Sport).filter(Sport.sport_id == payload.sport_id).first()
        if sport is None:
            return jsonify(
                ErrorOut(error=f"Sport {payload.sport_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        # ── check uniqueness (name within same sport) ─────────────────────────
        duplicate = (
            db.query(Team)
            .filter(Team.name == payload.name, Team.sport_id == payload.sport_id)
            .first()
        )
        if duplicate:
            return jsonify(
                ErrorOut(error="A team with this name already exists in this sport.",
                         code="DUPLICATE_TEAM").model_dump()
            ), 409

        # ── create and persist ────────────────────────────────────────────────
        team = Team(
            sport_id     = payload.sport_id,
            name         = payload.name,
            country      = payload.country,
            founded_year = payload.founded_year,
            home_ground  = payload.home_ground,
            logo_url     = payload.logo_url,
        )
        db.add(team)
        db.commit()
        db.refresh(team)

        # reload with relationship
        team = (
            db.query(Team)
            .options(joinedload(Team.sport))
            .filter(Team.team_id == team.team_id)
            .first()
        )

        return jsonify(TeamOut.model_validate(team).model_dump(mode="json")), 201

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@teams_bp.route("/admin/teams/<int:team_id>", methods=["PUT"])
@require_auth
@require_role(["admin"])
def update_team(team_id: int):
    """
    PUT /api/v1/admin/teams/<id>
    ────────────────────────────
    Admin edits team details or uploads logo_url.
    Only supplied fields are updated (partial update semantics).

    Request body (JSON): TeamUpdate  (all fields optional)
        {
          "name":         "Arsenal FC",
          "country":      "England",
          "founded_year": 1886,
          "home_ground":  "Emirates Stadium",
          "logo_url":     "https://cdn.example.com/new-logo.png"
        }

    Response 200: TeamOut
    Response 400: ErrorOut  (validation error)
    Response 404: ErrorOut  (team not found)
    Response 409: ErrorOut  (new name already taken in same sport)
    """
    db = get_db()
    try:
        # ── fetch existing record ─────────────────────────────────────────────
        team = (
            db.query(Team)
            .options(joinedload(Team.sport))
            .filter(Team.team_id == team_id)
            .first()
        )

        if team is None:
            return jsonify(
                ErrorOut(error=f"Team {team_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        # ── validate body ─────────────────────────────────────────────────────
        try:
            payload = TeamUpdate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 400

        # ── uniqueness check if name is changing (exclude self) ───────────────
        new_name = payload.name if payload.name is not None else team.name
        if payload.name is not None and payload.name != team.name:
            duplicate = (
                db.query(Team)
                .filter(
                    Team.name     == new_name,
                    Team.sport_id == team.sport_id,
                    Team.team_id  != team_id,
                )
                .first()
            )
            if duplicate:
                return jsonify(
                    ErrorOut(error="Another team with this name already exists in this sport.",
                             code="DUPLICATE_TEAM").model_dump()
                ), 409

        # ── apply updates ─────────────────────────────────────────────────────
        if payload.name         is not None: team.name         = payload.name
        if payload.country      is not None: team.country      = payload.country
        if payload.founded_year is not None: team.founded_year = payload.founded_year
        if payload.home_ground  is not None: team.home_ground  = payload.home_ground
        if payload.logo_url     is not None: team.logo_url     = payload.logo_url

        db.commit()
        db.refresh(team)

        return jsonify(TeamOut.model_validate(team).model_dump(mode="json")), 200

    finally:
        db.close()