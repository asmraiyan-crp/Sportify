"""
leagues.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for League resources.

Registered with the app under prefix /api/v1
so all routes here are relative to that.

Public endpoints:
    GET  /leagues                   – list leagues, optional ?sport_id= filter
    GET  /leagues/<id>              – single league with sport info
    GET  /leagues/<id>/standings    – live standings computed from game_match

Admin-only endpoints  (require role == 'admin' via @require_admin):
    POST /admin/leagues             – create a new league
    PUT  /admin/leagues/<id>        – edit league name / season

Dependencies (install once):
    pip install flask sqlalchemy pydantic[email] pyjwt bcrypt

Database session, JWT helpers, and error utilities are expected from:
    app.extensions  →  db  (SQLAlchemy session)
    app.auth        →  require_auth, require_admin decorators
    app.errors      →  not_found, validation_error, conflict_error

Standings query:
    The standings are computed purely in Python from finished game_match rows.
    If you later add a PostgreSQL function get_standings(league_id) you can
    swap the helper below with a raw SQL call:
        db.session.execute(text("SELECT * FROM get_standings(:lid)"), {"lid": league_id})
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, request, g
from pydantic import ValidationError
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload
from database import SessionLocal
# ── local imports (adjust paths to match your project layout) ─────────────────
from model.model import League, Sport, Team, GameMatch, TeamLeague
from model.schemas import (
    LeagueOut,
    LeagueCreate,
    LeagueUpdate,
    LeagueNested,
    StandingRow,
    StandingsOut,
    MessageOut,
    ErrorOut,
    PaginationMeta,
)

# If you have auth decorators, import them:
# from auth import require_auth, require_admin
# For now we define lightweight stubs so the file is self-contained.
from functools import wraps


# ─── Blueprint ────────────────────────────────────────────────────────────────

# leagues_bp = Blueprint("leagues", __name__)
leagues_bp = Blueprint("leagues", __name__, url_prefix="/leagues")


# ─── Auth decorator stubs (replace with real implementations) ─────────────────

def require_auth(f):
    """Verify JWT and set g.current_user.  Replace with your real decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # TODO: parse Authorization header, verify JWT, populate g.current_user
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Ensure g.current_user.role == 'admin'.  Replace with your real decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if user is None or user.role != "admin":
            return jsonify(ErrorOut(error="Forbidden", code="NOT_ADMIN").model_dump()), 403
        return f(*args, **kwargs)
    return decorated


# ─── DB session helper (replace with your app's db session) ───────────────────

# def get_db():
#     """Return the active SQLAlchemy session.  Replace with your real helper."""
#     from flask import current_app
#     return current_app.extensions["sqlalchemy"].db.session

def get_db():
    """Get database session."""
    return SessionLocal()


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@leagues_bp.route("/leagues", methods=["GET"])
def list_leagues():
    """
    GET /api/v1/leagues
    ───────────────────
    List all leagues.  Supports optional query parameters:

        ?sport_id=<int>   – filter by sport
        ?page=<int>       – page number (default 1)
        ?limit=<int>      – results per page (default 20, max 100)

    Response 200:
        {
          "data":  [ LeagueOut, … ],
          "meta":  PaginationMeta
        }
    """
    db = get_db()
    #return jsonify({"data": "data", "meta": "meta"}), 200

    # ── parse query params ────────────────────────────────────────────────────
    try:
        sport_id = int(request.args["sport_id"]) if "sport_id" in request.args else None
        page     = max(1, int(request.args.get("page",  1)))
        limit    = min(100, max(1, int(request.args.get("limit", 20))))
    except (ValueError, TypeError):
        return jsonify(ErrorOut(error="Invalid query parameter", code="BAD_QUERY").model_dump()), 400

    # ── build query ───────────────────────────────────────────────────────────
    q = db.query(League).options(joinedload(League.sport))

    if sport_id:
        q = q.filter(League.sport_id == sport_id)

    total   = q.count()
    leagues = q.order_by(League.name).offset((page - 1) * limit).limit(limit).all()

    # ── serialise ─────────────────────────────────────────────────────────────
    data = [LeagueOut.model_validate(lg).model_dump(mode="json") for lg in leagues]

    total_pages = max(1, (total + limit - 1) // limit)
    meta = PaginationMeta(
        page=page, limit=limit, total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    ).model_dump()

    return jsonify({"data": data, "meta": meta}), 200


# ─────────────────────────────────────────────────────────────────────────────

@leagues_bp.route("/leagues/<int:league_id>", methods=["GET"])
def get_league(league_id: int):
    """
    GET /api/v1/leagues/<id>
    ────────────────────────
    Single league detail including nested sport info.

    Response 200: LeagueOut
    Response 404: ErrorOut
    """
    db = get_db()

    league = (
        db.query(League)
        .options(joinedload(League.sport))
        .filter(League.league_id == league_id)
        .first()
    )

    if league is None:
        return jsonify(ErrorOut(error=f"League {league_id} not found", code="NOT_FOUND").model_dump()), 404

    return jsonify(LeagueOut.model_validate(league).model_dump(mode="json")), 200


# ─────────────────────────────────────────────────────────────────────────────

@leagues_bp.route("/leagues/<int:league_id>/standings", methods=["GET"])
def get_standings(league_id: int):
    """
    GET /api/v1/leagues/<id>/standings
    ───────────────────────────────────
    Compute and return the league table from finished game_match rows.

    The calculation follows standard football standings:
        points  = win×3 + draw×1
        tiebreak= points → goal_difference → goals_for → name

    If you have a get_standings() PostgreSQL function you can replace the
    Python computation below with:
        rows = db.session.execute(
            text("SELECT * FROM get_standings(:lid)"), {"lid": league_id}
        ).mappings().all()

    Response 200: StandingsOut
    Response 404: ErrorOut
    """
    db = get_db()

    league = (
        db.query(League)
        .options(joinedload(League.sport))
        .filter(League.league_id == league_id)
        .first()
    )

    if league is None:
        return jsonify(ErrorOut(error=f"League {league_id} not found", code="NOT_FOUND").model_dump()), 404

    # ── fetch all finished matches in this league ─────────────────────────────
    matches = (
        db.query(GameMatch)
        .options(
            joinedload(GameMatch.home_team),
            joinedload(GameMatch.away_team),
        )
        .filter(
            GameMatch.league_id == league_id,
            GameMatch.status    == "finished",
        )
        .all()
    )

    # ── aggregate stats per team ──────────────────────────────────────────────
    stats: dict[int, dict[str, Any]] = defaultdict(lambda: {
        "team_id": None, "team_name": "", "logo_url": None,
        "played": 0, "won": 0, "drawn": 0, "lost": 0,
        "gf": 0, "ga": 0,
    })

    def _ensure(team):
        s = stats[team.team_id]
        s["team_id"]   = team.team_id
        s["team_name"] = team.name
        s["logo_url"]  = team.logo_url

    for m in matches:
        ht, at = m.home_team, m.away_team
        hs, as_ = (m.home_score or 0), (m.away_score or 0)

        _ensure(ht); _ensure(at)

        stats[ht.team_id]["played"] += 1
        stats[at.team_id]["played"] += 1
        stats[ht.team_id]["gf"]     += hs
        stats[ht.team_id]["ga"]     += as_
        stats[at.team_id]["gf"]     += as_
        stats[at.team_id]["ga"]     += hs

        if hs > as_:                          # home win
            stats[ht.team_id]["won"]  += 1
            stats[at.team_id]["lost"] += 1
        elif hs < as_:                         # away win
            stats[at.team_id]["won"]  += 1
            stats[ht.team_id]["lost"] += 1
        else:                                  # draw
            stats[ht.team_id]["drawn"] += 1
            stats[at.team_id]["drawn"] += 1

    # ── sort: pts desc → gd desc → gf desc → name asc ────────────────────────
    def _pts(s):  return s["won"] * 3 + s["drawn"]
    def _gd(s):   return s["gf"] - s["ga"]

    rows_sorted = sorted(
        stats.values(),
        key=lambda s: (-_pts(s), -_gd(s), -s["gf"], s["team_name"]),
    )

    # ── build StandingRow objects ─────────────────────────────────────────────
    standing_rows = [
        StandingRow(
            pos      = pos + 1,
            team_id  = s["team_id"],
            team_name= s["team_name"],
            logo_url = s["logo_url"],
            played   = s["played"],
            won      = s["won"],
            drawn    = s["drawn"],
            lost     = s["lost"],
            gf       = s["gf"],
            ga       = s["ga"],
            gd       = _gd(s),
            pts      = _pts(s),
        )
        for pos, s in enumerate(rows_sorted)
    ]

    response = StandingsOut(
        league     = LeagueNested.model_validate(league),
        standings  = standing_rows,
        updated_at = datetime.now(tz=timezone.utc),
    )

    return jsonify(response.model_dump(mode="json")), 200


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@leagues_bp.route("/admin/leagues", methods=["POST"])
@require_auth
@require_admin
def create_league():
    """
    POST /api/v1/admin/leagues
    ──────────────────────────
    Admin creates a new league.

    Request body (JSON): LeagueCreate
        {
          "sport_id": 1,
          "name":     "Premier League",
          "country":  "England",
          "season":   "2024-25"
        }

    Response 201: LeagueOut
    Response 400: ErrorOut  (validation error)
    Response 404: ErrorOut  (sport not found)
    Response 409: ErrorOut  (duplicate league name+season)
    """
    db = get_db()

    # ── validate request body ─────────────────────────────────────────────────
    try:
        payload = LeagueCreate.model_validate(request.get_json(force=True) or {})
    except ValidationError as exc:
        return jsonify(
            ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                     details=exc.errors()).model_dump()
        ), 400

    # ── verify sport exists ───────────────────────────────────────────────────
    sport = db.query(Sport).filter(Sport.sport_id == payload.sport_id).first()
    if sport is None:
        return jsonify(ErrorOut(error=f"Sport {payload.sport_id} not found", code="NOT_FOUND").model_dump()), 404

    # ── check uniqueness (name + season) ─────────────────────────────────────
    duplicate = (
        db.query(League)
        .filter(League.name == payload.name, League.season == payload.season)
        .first()
    )
    if duplicate:
        return jsonify(
            ErrorOut(error="A league with this name and season already exists.",
                     code="DUPLICATE_LEAGUE").model_dump()
        ), 409

    # ── create and persist ────────────────────────────────────────────────────
    league = League(
        sport_id = payload.sport_id,
        name     = payload.name,
        country  = payload.country,
        season   = payload.season,
    )
    db.add(league)
    db.commit()
    db.refresh(league)

    # reload with relationship
    league = (
        db.query(League)
        .options(joinedload(League.sport))
        .filter(League.league_id == league.league_id)
        .first()
    )

    return jsonify(LeagueOut.model_validate(league).model_dump(mode="json")), 201


# ─────────────────────────────────────────────────────────────────────────────

@leagues_bp.route("/admin/leagues/<int:league_id>", methods=["PUT"])
@require_auth
@require_admin
def update_league(league_id: int):
    """
    PUT /api/v1/admin/leagues/<id>
    ──────────────────────────────
    Admin edits league name and/or season.  Only supplied fields are updated
    (partial update semantics even though the method is PUT).

    Request body (JSON): LeagueUpdate  (all fields optional)
        {
          "name":    "EFL Championship",
          "season":  "2025-26",
          "country": "England"
        }

    Response 200: LeagueOut
    Response 400: ErrorOut  (validation error)
    Response 404: ErrorOut  (league not found)
    Response 409: ErrorOut  (new name+season already taken)
    """
    db = get_db()

    # ── fetch existing record ─────────────────────────────────────────────────
    league = (
        db.query(League)
        .options(joinedload(League.sport))
        .filter(League.league_id == league_id)
        .first()
    )

    if league is None:
        return jsonify(ErrorOut(error=f"League {league_id} not found", code="NOT_FOUND").model_dump()), 404

    # ── validate body ─────────────────────────────────────────────────────────
    try:
        payload = LeagueUpdate.model_validate(request.get_json(force=True) or {})
    except ValidationError as exc:
        return jsonify(
            ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                     details=exc.errors()).model_dump()
        ), 400

    # ── determine target values after update ──────────────────────────────────
    new_name   = payload.name   if payload.name   is not None else league.name
    new_season = payload.season if payload.season is not None else league.season

    # ── uniqueness check (excluding self) ─────────────────────────────────────
    duplicate = (
        db.query(League)
        .filter(
            League.name      == new_name,
            League.season    == new_season,
            League.league_id != league_id,       # exclude current row
        )
        .first()
    )
    if duplicate:
        return jsonify(
            ErrorOut(error="Another league with this name and season already exists.",
                     code="DUPLICATE_LEAGUE").model_dump()
        ), 409

    # ── apply updates ─────────────────────────────────────────────────────────
    if payload.name    is not None: league.name    = payload.name
    if payload.season  is not None: league.season  = payload.season
    if payload.country is not None: league.country = payload.country

    db.commit()
    db.refresh(league)

    return jsonify(LeagueOut.model_validate(league).model_dump(mode="json")), 200


# ══════════════════════════════════════════════════════════════════════════════
# BLUEPRINT REGISTRATION HELPER
# ══════════════════════════════════════════════════════════════════════════════

def register_leagues_bp(app, url_prefix: str = "/api/v1"):
    """
    Call this once inside your application factory:

        from leagues import register_leagues_bp
        register_leagues_bp(app)

    All routes will be served under /api/v1/leagues and /api/v1/admin/leagues.
    """
    app.register_blueprint(leagues_bp, url_prefix=url_prefix)