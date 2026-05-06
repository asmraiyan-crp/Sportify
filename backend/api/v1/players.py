"""
players.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Player resources.

Registered with the app under prefix /api/v1.

Public endpoints:
    GET  /players                   – list players; ?sport_id= ?team_id= ?name= filters
    GET  /players/<id>              – player profile
    GET  /players/<id>/stats        – season stats aggregated from player_match_stat
    GET  /players/<id>/ratings      – average fan rating across all matches

Auth-required endpoints:
    POST /players/<id>/rate         – fan submits 1-5 star rating for a player in a match

Manager-only endpoint:
    PUT  /players/<id>/injury       – update injury_status
                                      verifies profiles.team_managed == player.team_id
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request, g
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import SessionLocal
from model.model import Player, Sport, Team, PlayerMatchStat, PlayerRating, Profile
from model.schemas import (
    PlayerOut,
    PlayerRatingOut,
    PlayerRatingCreate,
    PlayerRatingAvg,
    InjuryUpdate,
    ErrorOut,
    PaginationMeta,
)
from core.auth import require_auth, require_role


# ─── Blueprint ────────────────────────────────────────────────────────────────

players_bp = Blueprint("players", __name__)


# ─── DB helper ───────────────────────────────────────────────────────────────

def get_db():
    return SessionLocal()


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@players_bp.route("/players", methods=["GET"])
def list_players():
    """
    GET /api/v1/players
    ───────────────────
    List all players. Supports optional query parameters:

        ?sport_id=<int>   – filter by sport
        ?team_id=<int>    – filter by team
        ?name=<str>       – case-insensitive partial match on player name
        ?page=<int>       – page number (default 1)
        ?limit=<int>      – results per page (default 20, max 100)

    Response 200:
        {
          "data": [ PlayerOut, … ],
          "meta": PaginationMeta
        }
    """
    db = get_db()
    try:
        # ── parse query params ────────────────────────────────────────────────
        try:
            sport_id = int(request.args["sport_id"]) if "sport_id" in request.args else None
            team_id  = int(request.args["team_id"])  if "team_id"  in request.args else None
            page     = max(1, int(request.args.get("page",  1)))
            limit    = min(100, max(1, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            return jsonify(ErrorOut(error="Invalid query parameter", code="BAD_QUERY").model_dump()), 400

        name_q = request.args.get("name", "").strip()

        # ── build query ───────────────────────────────────────────────────────
        q = db.query(Player).options(
            joinedload(Player.team),
            joinedload(Player.sport),
        )

        if sport_id:
            q = q.filter(Player.sport_id == sport_id)
        if team_id:
            q = q.filter(Player.team_id == team_id)
        if name_q:
            q = q.filter(Player.name.ilike(f"%{name_q}%"))

        total   = q.count()
        players = q.order_by(Player.name).offset((page - 1) * limit).limit(limit).all()

        # ── serialise ─────────────────────────────────────────────────────────
        data = [PlayerOut.model_validate(p).model_dump(mode="json") for p in players]

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

@players_bp.route("/players/<int:player_id>", methods=["GET"])
def get_player(player_id: int):
    """
    GET /api/v1/players/<id>
    ────────────────────────
    Player profile: name, nationality, DOB, position, injury_status, logo.

    Response 200: PlayerOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        player = (
            db.query(Player)
            .options(joinedload(Player.team), joinedload(Player.sport))
            .filter(Player.player_id == player_id)
            .first()
        )

        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

        return jsonify(PlayerOut.model_validate(player).model_dump(mode="json")), 200

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@players_bp.route("/players/<int:player_id>/stats", methods=["GET"])
def get_player_stats(player_id: int):
    """
    GET /api/v1/players/<id>/stats
    ──────────────────────────────
    Season stats aggregated from player_match_stat.

    Sums: minutes_played, goals, assists, yellow_cards, red_cards,
          runs_scored, wickets across all recorded matches.

    Response 200:
        {
          "player_id":      1,
          "player_name":    "Bukayo Saka",
          "matches_played": 30,
          "minutes_played": 2430,
          "goals":          14,
          "assists":        11,
          "yellow_cards":   2,
          "red_cards":      0,
          "runs_scored":    0,
          "wickets":        0
        }
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        player = db.query(Player).filter(Player.player_id == player_id).first()

        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

        # ── aggregate stats ───────────────────────────────────────────────────
        agg = (
            db.query(
                func.count(PlayerMatchStat.stat_id)   .label("matches_played"),
                func.sum(PlayerMatchStat.minutes_played).label("minutes_played"),
                func.sum(PlayerMatchStat.goals)         .label("goals"),
                func.sum(PlayerMatchStat.assists)       .label("assists"),
                func.sum(PlayerMatchStat.yellow_cards)  .label("yellow_cards"),
                func.sum(PlayerMatchStat.red_cards)     .label("red_cards"),
                func.sum(PlayerMatchStat.runs_scored)   .label("runs_scored"),
                func.sum(PlayerMatchStat.wickets)       .label("wickets"),
            )
            .filter(PlayerMatchStat.player_id == player_id)
            .one()
        )

        return jsonify({
            "player_id":      player.player_id,
            "player_name":    player.name,
            "matches_played": agg.matches_played or 0,
            "minutes_played": agg.minutes_played or 0,
            "goals":          agg.goals          or 0,
            "assists":        agg.assists         or 0,
            "yellow_cards":   agg.yellow_cards    or 0,
            "red_cards":      agg.red_cards       or 0,
            "runs_scored":    agg.runs_scored     or 0,
            "wickets":        agg.wickets         or 0,
        }), 200

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@players_bp.route("/players/<int:player_id>/ratings", methods=["GET"])
def get_player_ratings(player_id: int):
    """
    GET /api/v1/players/<id>/ratings
    ─────────────────────────────────
    Average fan rating for this player across all matches.

    Response 200: PlayerRatingAvg
        {
          "player_id":      1,
          "average_rating": 4.2,
          "total_ratings":  87
        }
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        player = db.query(Player).filter(Player.player_id == player_id).first()

        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

        agg = (
            db.query(
                func.avg(PlayerRating.rating).label("avg_rating"),
                func.count(PlayerRating.rating_id).label("total"),
            )
            .filter(PlayerRating.player_id == player_id)
            .one()
        )

        result = PlayerRatingAvg(
            player_id      = player.player_id,
            average_rating = round(float(agg.avg_rating), 2) if agg.avg_rating else None,
            total_ratings  = agg.total or 0,
        )

        return jsonify(result.model_dump()), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# AUTH-REQUIRED ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@players_bp.route("/players/<int:player_id>/rate", methods=["POST"])
@require_auth
def rate_player(player_id: int):
    """
    POST /api/v1/players/<id>/rate
    ──────────────────────────────
    Fan submits a 1-5 star rating for a player in a specific match.
    A user can only rate a player once per match (unique constraint enforced in DB).

    Request body:
        {
          "player_id": 1,      ← must match the URL param
          "match_id":  42,
          "rating":    4
        }

    Response 201: PlayerRatingOut
    Response 400: ErrorOut  (validation error or player_id mismatch)
    Response 404: ErrorOut  (player not found)
    Response 409: ErrorOut  (already rated this player in this match)
    """
    db = get_db()
    try:
        # ── validate body ─────────────────────────────────────────────────────
        try:
            payload = PlayerRatingCreate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 400

        # ── player_id in body must match URL ──────────────────────────────────
        if payload.player_id != player_id:
            return jsonify(
                ErrorOut(error="player_id in body does not match URL parameter.",
                         code="PLAYER_ID_MISMATCH").model_dump()
            ), 400

        # ── verify player exists ──────────────────────────────────────────────
        player = db.query(Player).filter(Player.player_id == player_id).first()
        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

        # ── get current user from JWT (set by @require_auth) ──────────────────
        user_id = g.user.get("sub")

        # ── check for duplicate rating ────────────────────────────────────────
        existing = (
            db.query(PlayerRating)
            .filter(
                PlayerRating.player_id == player_id,
                PlayerRating.match_id  == payload.match_id,
                PlayerRating.user_id   == user_id,
            )
            .first()
        )
        if existing:
            return jsonify(
                ErrorOut(error="You have already rated this player for this match.",
                         code="DUPLICATE_RATING").model_dump()
            ), 409

        # ── create rating ─────────────────────────────────────────────────────
        new_rating = PlayerRating(
            player_id = player_id,
            match_id  = payload.match_id,
            user_id   = user_id,
            rating    = payload.rating,
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)

        # reload with user relationship for response
        new_rating = (
            db.query(PlayerRating)
            .options(joinedload(PlayerRating.user))
            .filter(PlayerRating.rating_id == new_rating.rating_id)
            .first()
        )

        return jsonify(PlayerRatingOut.model_validate(new_rating).model_dump(mode="json")), 201

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# MANAGER-ONLY ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@players_bp.route("/players/<int:player_id>/injury", methods=["PUT"])
@require_auth
@require_role(["admin", "team_manager"])
def update_injury(player_id: int):
    """
    PUT /api/v1/players/<id>/injury
    ────────────────────────────────
    Update a player's injury_status.

    Business rule (FR-25):
        A team_manager may only update players in their own team.
        profiles.team_managed must equal player.team_id.
        Admins bypass this restriction.

    Request body:
        {
          "injury_status": "injured"    ← one of: "fit" | "injured" | "doubtful"
        }

    Response 200: PlayerOut
    Response 400: ErrorOut  (validation error)
    Response 403: ErrorOut  (manager trying to update another team's player)
    Response 404: ErrorOut  (player not found)
    """
    db = get_db()
    try:
        # ── validate body ─────────────────────────────────────────────────────
        try:
            payload = InjuryUpdate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 400

        # ── fetch player ──────────────────────────────────────────────────────
        player = (
            db.query(Player)
            .options(joinedload(Player.team), joinedload(Player.sport))
            .filter(Player.player_id == player_id)
            .first()
        )

        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

        # ── FR-25: team_manager ownership check ───────────────────────────────
        caller_role = g.user.get("role")
        if caller_role == "team_manager":
            caller_id = g.user.get("sub")
            profile = db.query(Profile).filter(Profile.id == caller_id).first()

            if profile is None or profile.team_managed != player.team_id:
                return jsonify(
                    ErrorOut(
                        error="You are not authorised to update players outside your managed team.",
                        code="WRONG_TEAM"
                    ).model_dump()
                ), 403

        # ── apply update ──────────────────────────────────────────────────────
        from datetime import datetime, timezone
        player.injury_status     = payload.injury_status
        player.injury_updated_at = datetime.now(tz=timezone.utc)

        db.commit()
        db.refresh(player)

        return jsonify(PlayerOut.model_validate(player).model_dump(mode="json")), 200

    finally:
        db.close()