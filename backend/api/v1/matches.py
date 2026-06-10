"""
matches.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Match resources.

Registered with the app under prefix /api/v1
so all routes here are relative to that.

Public endpoints:
    GET  /matches                    – list matches with filters
    GET  /matches/live               – all live matches
    GET  /matches/<id>               – full match detail
    GET  /matches/<id>/highlights    – highlight videos for match
    GET  /matches/<id>/player-stats  – player performance stats for match
    GET  /matches/<id>/reviews       – reviews + AVG(rating)

Authenticated endpoints:
    POST /matches/<id>/reviews       – fan posts a review (unique per user+match)

Admin-only endpoints:
    POST   /admin/highlights         – add a highlight
    DELETE /admin/highlights/<id>    – remove a highlight
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy import func, text
from sqlalchemy.orm import joinedload

from core.auth import require_auth, require_role
from database import SessionLocal
from model.model import GameMatch, Highlight, PlayerMatchStat, Profile, Review
from model.schemas import (
    ErrorOut,
    HighlightCreate,
    HighlightOut,
    MatchDetailOut,
    MatchListFilter,
    MatchOut,
    MessageOut,
    PaginationMeta,
    ReviewCreate,
    ReviewOut,
    ReviewWithStats,
)

matches_bp = Blueprint("matches", __name__)


# ─── DB helper ────────────────────────────────────────────────────────────────

def get_db():
    return SessionLocal()


# ─── eager-load options reused across routes ──────────────────────────────────

_MATCH_LOAD = [
    joinedload(GameMatch.league),
    joinedload(GameMatch.home_team),
    joinedload(GameMatch.away_team),
]

_MATCH_DETAIL_LOAD = _MATCH_LOAD + [
    joinedload(GameMatch.player_stats).joinedload(PlayerMatchStat.player),
    joinedload(GameMatch.highlights),
]


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("", methods=["GET"])
def get_all_matches():
    from database import get_db
    from psycopg2.extras import RealDictCursor
    from flask import request, jsonify

    try:
        status = request.args.get("status")
        limit = request.args.get("limit", 20, type=int)
        team_id = request.args.get("team_id", type=int)

        # 🚀 FIXED: We JOIN the view with the raw game_match table to get the IDs
        query = """
            SELECT v.*, m.home_team_id, m.away_team_id 
            FROM v_match_detail v
            JOIN game_match m ON v.match_id = m.match_id
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND v.status = %s"
            params.append(status)

        if team_id:
            # Now we can safely filter by the raw IDs!
            query += " AND (m.home_team_id = %s OR m.away_team_id = %s)"
            params.extend([team_id, team_id])

        query += " ORDER BY v.match_datetime DESC LIMIT %s"
        params.append(limit)

        with get_db() as db:
            with db.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                results = cur.fetchall()
                
                return jsonify({"data": [dict(row) for row in results]}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



# Paste this in api/v1/matches.py:

@matches_bp.route("/search", methods=["GET"])
def search_matches_endpoint():
    from database import get_db
    from psycopg2.extras import RealDictCursor
    from flask import request, jsonify

    try:
        team_name = request.args.get("team_name")
        player_name = request.args.get("player_name")
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        league_id = request.args.get("league_id", type=int)
        status = request.args.get("status")

        with get_db() as db:
            with db.cursor(cursor_factory=RealDictCursor) as cur:
                # 🚀 FIXED: We wrapped your function in a SELECT that JOINs the game_match table to grab the IDs!
                query = """
                    SELECT s.*, m.home_team_id, m.away_team_id 
                    FROM search_matches(
                        p_team_name := %s,
                        p_player_name := %s,
                        p_date_from := %s,
                        p_date_to := %s,
                        p_league_id := %s,
                        p_status := %s
                    ) s
                    JOIN game_match m ON s.match_id = m.match_id
                """
                
                cur.execute(query, (team_name, player_name, date_from, date_to, league_id, status))
                results = cur.fetchall()
                
                return jsonify({"data": [dict(row) for row in results]}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "code": "DB_ERROR"}), 500

# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches/live
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/live", methods=["GET"])
def list_live_matches():
    from psycopg2.extras import RealDictCursor
    from database import get_db

    try:
        sport = request.args.get("sport")

        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # Use v.* to keep all original view columns, then alias the gm
            # IDs so they overwrite any NULLs the view returns for those fields.
            cur.execute("""
                SELECT
                    v.*,
                    gm.home_team_id AS home_team_id,
                    gm.away_team_id AS away_team_id
                FROM v_live_matches v
                JOIN game_match gm ON gm.match_id = v.match_id
                WHERE (%s IS NULL OR v.sport_name = %s)
                ORDER BY v.match_datetime DESC
            """, (sport, sport))

            results = cur.fetchall()
            data = [dict(row) for row in results]

            return jsonify({"data": data, "total": len(data)}), 200

    except Exception as e:
        return jsonify(
            ErrorOut(error=str(e), code="DB_ERROR").model_dump()
        ), 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches/<id>
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/<int:match_id>", methods=["GET"])
def get_match(match_id: int):
    from psycopg2.extras import RealDictCursor
    from database import get_db

    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT
                    v.*,
                    gm.home_team_id AS home_team_id,
                    gm.away_team_id AS away_team_id
                FROM v_match_detail v
                JOIN game_match gm ON gm.match_id = v.match_id
                WHERE v.match_id = %s
            """, (match_id,))

            result = cur.fetchone()

            if result is None:
                return jsonify(
                    ErrorOut(error=f"Match {match_id} not found", code="NOT_FOUND").model_dump()
                ), 404

            return jsonify(dict(result)), 200

    except Exception as e:
        return jsonify(
            ErrorOut(error=str(e), code="DB_ERROR").model_dump()
        ), 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches/<id>/highlights
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/<int:match_id>/highlights", methods=["GET"])
def get_match_highlights(match_id: int):
    """
    Highlight video URLs for a match.

    Response 200: { "data": [HighlightOut, …] }
    Response 404: ErrorOut  (match not found)
    """
    db = get_db()
    try:
        match = db.query(GameMatch).filter(GameMatch.match_id == match_id).first()
        if match is None:
            return jsonify(
                ErrorOut(error=f"Match {match_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        highlights = (
            db.query(Highlight)
            .filter(Highlight.match_id == match_id)
            .order_by(Highlight.created_at.desc())
            .all()
        )

        data = [HighlightOut.model_validate(h).model_dump(mode="json") for h in highlights]
        return jsonify({"data": data}), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches/<id>/player-stats
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/<int:match_id>/player-stats", methods=["GET"])
def get_match_player_stats(match_id: int):
    """
    All player stats for a match, sorted by goals descending.

    Response 200:
        { "data": [player_stat_row, …], "total": <int> }
    Response 404: ErrorOut  (match not found)
    """
    db = get_db()
    try:
        match = db.query(GameMatch).filter(GameMatch.match_id == match_id).first()
        if match is None:
            return jsonify(
                ErrorOut(error=f"Match {match_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        query = text("""
            SELECT
                p.name, p.position_role, p.profile_image_url,
                pms.goals, pms.assists, pms.minutes_played,
                pms.yellow_cards, pms.red_cards
            FROM player_match_stat pms
            JOIN player     p ON p.player_id = pms.player_id
            JOIN game_match m ON m.match_id  = pms.match_id
            WHERE pms.match_id = :match_id
            ORDER BY pms.goals DESC
        """)

        results = db.execute(query, {"match_id": match_id}).fetchall()
        data = [dict(row._mapping) for row in results]

        return jsonify({"data": data, "total": len(data)}), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches/<id>/reviews
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/<int:match_id>/reviews", methods=["GET"])
def get_match_reviews(match_id: int):
    """
    All reviews for a match plus AVG(rating) using get_match_review_summary() function.

    Response 200: { "average_rating": ..., "total_reviews": ..., "reviews": [...] }
    Response 404: ErrorOut  (match not found)
    """
    from psycopg2.extras import RealDictCursor
    from database import get_db

    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT match_id FROM game_match WHERE match_id = %s", (match_id,))
            if not cur.fetchone():
                return jsonify(
                    ErrorOut(error=f"Match {match_id} not found", code="NOT_FOUND").model_dump()
                ), 404

            cur.execute("SELECT * FROM get_match_review_summary(%s)", (match_id,))
            results = cur.fetchall()

            if not results:
                return jsonify({
                    "average_rating": None,
                    "total_reviews": 0,
                    "reviews": []
                }), 200

            first_row = results[0]

            response = {
                "average_rating": first_row.get("average_rating"),
                "total_reviews": first_row.get("total_reviews", len(results)),
                "reviews": [dict(row) for row in results]
            }

            return jsonify(response), 200

    except Exception as e:
        return jsonify(
            ErrorOut(error=str(e), code="DB_ERROR").model_dump()
        ), 500


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/matches/<id>/reviews
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/<int:match_id>/reviews", methods=["POST"])
@require_auth
def post_match_review(match_id: int):
    """
    Fan posts a review for a match.
    One review per user per match — 409 on duplicate.

    Request body: { "rating": 1-5, "body": "..." }
    Response 201: ReviewOut
    Response 404: ErrorOut  (match not found)
    Response 409: ErrorOut  (duplicate review)
    """
    db = get_db()
    try:
        user_id = g.user.get("sub")

        match = db.query(GameMatch).filter(GameMatch.match_id == match_id).first()
        if match is None:
            return jsonify(
                ErrorOut(error=f"Match {match_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        existing = (
            db.query(Review)
            .filter(Review.match_id == match_id, Review.user_id == user_id)
            .first()
        )
        if existing:
            return jsonify(
                ErrorOut(
                    error="You have already reviewed this match.",
                    code="DUPLICATE_REVIEW"
                ).model_dump()
            ), 409

        try:
            payload = ReviewCreate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 422

        review = Review(
            match_id=match_id,
            user_id=user_id,
            rating=payload.rating,
            body=payload.body,
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        review = (
            db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.review_id == review.review_id)
            .first()
        )

        return jsonify(ReviewOut.model_validate(review).model_dump(mode="json")), 201

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/admin/highlights
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/admin/highlights", methods=["POST"])
@require_auth
@require_role(["admin"])
def create_highlight():
    """
    Admin adds a highlight for a match.

    Request body: { "match_id": <int>, "title": "...", "video_url": "..." }
    Response 201: HighlightOut
    Response 404: ErrorOut  (match not found)
    """
    db = get_db()
    try:
        try:
            payload = HighlightCreate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 422

        match = db.query(GameMatch).filter(GameMatch.match_id == payload.match_id).first()
        if match is None:
            return jsonify(
                ErrorOut(error=f"Match {payload.match_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        user_id = g.user.get("sub")
        highlight = Highlight(
            match_id=payload.match_id,
            title=payload.title,
            video_url=payload.video_url,
            added_by=user_id,
        )
        db.add(highlight)
        db.commit()
        db.refresh(highlight)

        return jsonify(HighlightOut.model_validate(highlight).model_dump(mode="json")), 201

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/admin/highlights/<id>
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/admin/highlights/<int:highlight_id>", methods=["DELETE"])
@require_auth
@require_role(["admin"])
def delete_highlight(highlight_id: int):
    """
    Admin removes a highlight.

    Response 200: MessageOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        highlight = db.query(Highlight).filter(Highlight.highlight_id == highlight_id).first()
        if highlight is None:
            return jsonify(
                ErrorOut(error=f"Highlight {highlight_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        db.delete(highlight)
        db.commit()

        return jsonify(MessageOut(message=f"Highlight {highlight_id} deleted.").model_dump()), 200

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()


@matches_bp.route("/feed", methods=["GET"])
@require_auth
def get_personalized_feed():
    from database import get_db
    from psycopg2.extras import RealDictCursor

    # db is already your raw psycopg2 connection!
    with get_db() as db: 
        try:
            user_id = g.user.get("sub")
            
            # Create a cursor from the connection
            with db.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM get_user_feed(%s)", (user_id,))
                results = cur.fetchall()
                
                return jsonify({"data": [dict(row) for row in results]}), 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e), "code": "DB_ERROR"}), 500