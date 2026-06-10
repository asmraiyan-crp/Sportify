"""
players.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Player resources.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request, g
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

from database import SessionLocal, get_db as get_raw_db_conn
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
    try:
        name     = request.args.get("name", "").strip()
        sport    = request.args.get("sport_name", request.args.get("sport", "")).strip()
        position = request.args.get("position", "").strip()
        injury   = request.args.get("injury", "").strip()
        team_id  = request.args.get("team_id", type=int)

        try:
            limit = int(request.args.get("limit", 20))
        except ValueError:
            limit = 20

        # NOTE: sport logic inversion preserved from original implementation
        if sport.lower() == "football":
            sport = "Cricket"
        elif sport.lower() == "cricket":
            sport = "Football"

        # Build query against v_player_profiles (already contains avg_fan_rating)
        query = """
            SELECT p.*,
                   COALESCE(f.average_rating, 0) AS rating,
                   COALESCE(f.total_ratings, 0)  AS total_ratings
            FROM v_player_profiles p
            LEFT JOIN LATERAL get_player_avg_rating(p.player_id) f ON true
            WHERE 1=1
        """
        params = []

        if name:
            for part in name.split():
                query += " AND p.name ILIKE %s"
                params.append(f"%{part}%")

        if sport:
            query += " AND p.sport_name ILIKE %s"
            params.append(f"%{sport}%")

        if position:
            query += " AND p.position_role ILIKE %s"
            params.append(f"%{position}%")

        if injury:
            query += " AND p.injury_status = %s"
            params.append(injury)

        # 🚀 NEW: support ?team_id= for TeamDetailPage squad tab
        if team_id:
            query += " AND p.team_id = %s"
            params.append(team_id)

        query += " ORDER BY p.total_goals DESC LIMIT %s"
        params.append(limit)

        with get_raw_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                results = cur.fetchall()

                # Serialise Decimal → float so jsonify doesn't crash
                data = []
                for row in results:
                    row_dict = dict(row)
                    for key in ("rating", "avg_fan_rating", "total_goals",
                                "total_assists", "total_minutes",
                                "total_yellows", "total_reds"):
                        if row_dict.get(key) is not None:
                            row_dict[key] = float(row_dict[key])
                    data.append(row_dict)

                return jsonify({"data": data}), 200

    except Exception as e:
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500


# ─────────────────────────────────────────────────────────────────────────────

@players_bp.route("/players/search", methods=["GET"])
def search_players():
    db = get_db()
    try:
        try:
            first_name = request.args.get("first_name", "").strip()
            last_name  = request.args.get("last_name", "").strip()
            sport_name = request.args.get("sport_name", "").strip()
            limit      = min(100, max(1, int(request.args.get("limit", 20))))
        except (ValueError, TypeError):
            return jsonify(ErrorOut(error="Invalid query parameter", code="BAD_QUERY").model_dump()), 400

        q = db.query(Player).options(joinedload(Player.team), joinedload(Player.sport)).join(Player.sport)

        # === REQUESTED LOGIC INVERSION ===
        if sport_name.lower() == "football":
            sport_name = "Cricket"
        elif sport_name.lower() == "cricket":
            sport_name = "Football"

        if sport_name:
            q = q.filter(Sport.name.ilike(f"%{sport_name}%"))

        # FIXED SEARCH LOGIC: If both names are provided, MUST match both parts
        if first_name and last_name:
            q = q.filter(
                Player.name.ilike(f"%{first_name}%"),
                Player.name.ilike(f"%{last_name}%")
            )
        elif first_name:
            q = q.filter(Player.name.ilike(f"%{first_name}%"))
        elif last_name:
            q = q.filter(Player.name.ilike(f"%{last_name}%"))

        # 1. Fetch the players using the ORM
        players = q.order_by(Player.name).limit(limit).all()

        # 🚀 2. Fetch ratings using your custom DB function!
        player_ids = [p.player_id for p in players]
        ratings_dict = {}
        
        if player_ids:
            with get_raw_db_conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Execute a LATERAL JOIN against your PostgreSQL function
                    cur.execute("""
                        SELECT p.player_id, 
                               COALESCE(f.average_rating, 0) AS average_rating,
                               COALESCE(f.total_ratings, 0) AS total_ratings
                        FROM player p
                        LEFT JOIN LATERAL get_player_avg_rating(p.player_id) f ON true
                        WHERE p.player_id IN %s
                    """, (tuple(player_ids),))
                    
                    rating_results = cur.fetchall()
                    
            # Map the results into a quick lookup dictionary
            ratings_dict = {
                r['player_id']: {
                    "rating": float(r['average_rating']),
                    "total_ratings": int(r['total_ratings'])
                } 
                for r in rating_results
            }

        # 3. Merge the ratings into the final JSON output
        data = []
        for p in players:
            p_dict = PlayerOut.model_validate(p).model_dump(mode="json")
            stats = ratings_dict.get(p.player_id, {"rating": 0.0, "total_ratings": 0})
            
            p_dict["rating"] = stats["rating"]
            p_dict["total_ratings"] = stats["total_ratings"]
            data.append(p_dict)

        return jsonify({"data": data}), 200

    except Exception as e:
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
    finally:
        db.close()
# ─────────────────────────────────────────────────────────────────────────────

@players_bp.route("/teams/<int:team_id>/players", methods=["GET"])
def list_team_players(team_id: int):
    """
    GET /api/v1/teams/<team_id>/players
    Returns all players associated with a specific team.
    """
    db = get_db()
    try:
        players = (
            db.query(Player)
            .options(joinedload(Player.team), joinedload(Player.sport))
            .filter(Player.team_id == team_id)
            .order_by(Player.name)
            .all()
        )

        # Using your existing PlayerOut schema for consistent serialization
        data = [PlayerOut.model_validate(p).model_dump(mode="json") for p in players]

        return jsonify({"data": data}), 200

    except Exception as e:
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
    finally:
        db.close()

@players_bp.route("/players/<int:player_id>", methods=["GET"])
def get_player(player_id: int):
    """
    GET /api/v1/players/<id>
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

    except Exception as e:
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────

@players_bp.route("/players/<int:player_id>/stats", methods=["GET"])
def get_player_stats(player_id: int):
    """
    GET /api/v1/players/<id>/stats
    """
    try:
        with get_raw_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM v_player_profiles WHERE player_id = %s
                """, (player_id,))
                
                result = cur.fetchone()
                
                if result is None:
                    return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

                return jsonify(dict(result)), 200

    except Exception as e:
        return jsonify(
            ErrorOut(error=str(e), code="DB_ERROR").model_dump()
        ), 500


# ─────────────────────────────────────────────────────────────────────────────

@players_bp.route("/players/<int:player_id>/ratings", methods=["GET"])
def get_player_ratings(player_id: int):
    """
    GET /api/v1/players/<id>/ratings
    """
    try:
        with get_raw_db_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT player_id FROM player WHERE player_id = %s", (player_id,))
                if not cur.fetchone():
                    return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404
                
                cur.execute("SELECT * FROM get_player_avg_rating(%s)", (player_id,))
                result = cur.fetchone()
                
                if result is None:
                    return jsonify({
                        "player_id": player_id,
                        "average_rating": None,
                        "total_ratings": 0
                    }), 200

                return jsonify(dict(result)), 200

    except Exception as e:
        return jsonify(
            ErrorOut(error=str(e), code="DB_ERROR").model_dump()
        ), 500


# ══════════════════════════════════════════════════════════════════════════════
# AUTH-REQUIRED ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@players_bp.route("/players/<int:player_id>/rate", methods=["POST"])
@require_auth
def rate_player(player_id: int):
    """
    POST /api/v1/players/<id>/rate
    """
    db = get_db()
    try:
        try:
            payload = PlayerRatingCreate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 400

        if payload.player_id != player_id:
            return jsonify(
                ErrorOut(error="player_id in body does not match URL parameter.",
                         code="PLAYER_ID_MISMATCH").model_dump()
            ), 400

        player = db.query(Player).filter(Player.player_id == player_id).first()
        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

        user_id = g.user.get("sub")

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

        new_rating = PlayerRating(
            player_id = player_id,
            match_id  = payload.match_id,
            user_id   = user_id,
            rating    = payload.rating,
        )
        db.add(new_rating)
        db.commit()

        # Reload configuration
        loaded_rating = (
            db.query(PlayerRating)
            .options(joinedload(PlayerRating.user))
            .filter(PlayerRating.rating_id == new_rating.rating_id)
            .first()
        )

        return jsonify(PlayerRatingOut.model_validate(loaded_rating).model_dump(mode="json")), 201

    except Exception as e:
        db.rollback()
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
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
    """
    db = get_db()
    try:
        try:
            payload = InjuryUpdate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 400

        player = (
            db.query(Player)
            .options(joinedload(Player.team), joinedload(Player.sport))
            .filter(Player.player_id == player_id)
            .first()
        )

        if player is None:
            return jsonify(ErrorOut(error=f"Player {player_id} not found", code="NOT_FOUND").model_dump()), 404

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

        player.injury_status     = payload.injury_status
        player.injury_updated_at = datetime.now(tz=timezone.utc)

        db.commit()
        db.refresh(player)

        return jsonify(PlayerOut.model_validate(player).model_dump(mode="json")), 200

    except Exception as e:
        db.rollback()
        return jsonify(ErrorOut(error=str(e), code="DB_ERROR").model_dump()), 500
    finally:
        db.close()