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
from sqlalchemy import func
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
def list_matches():
    """
    List matches with optional filters.

    Query params:
        ?sport=<str>        filter by sport name (case-insensitive)
        ?league_id=<int>
        ?status=<str>       scheduled|live|finished|postponed|cancelled
        ?date_from=<date>   YYYY-MM-DD
        ?date_to=<date>     YYYY-MM-DD
        ?page=<int>         default 1
        ?limit=<int>        default 20, max 100

    Response 200:
        { "data": [MatchOut, …], "meta": PaginationMeta }
    """
    db = get_db()
    try:
        try:
            filters = MatchListFilter(
                sport=request.args.get("sport"),
                league_id=request.args.get("league_id"),
                status=request.args.get("status"),
                date_from=request.args.get("date_from"),
                date_to=request.args.get("date_to"),
                page=request.args.get("page", 1),
                limit=request.args.get("limit", 20),
            )
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Invalid query parameters", code="BAD_QUERY",
                         details=exc.errors()).model_dump()
            ), 400

        q = (
            db.query(GameMatch)
            .options(*_MATCH_LOAD)
        )

        if filters.sport:
            from model.model import League, Sport
            q = (
                q.join(GameMatch.league)
                 .join(League.sport)
                 .filter(func.lower(Sport.name) == filters.sport.lower())
            )

        if filters.league_id:
            q = q.filter(GameMatch.league_id == filters.league_id)

        if filters.status:
            q = q.filter(GameMatch.status == filters.status)

        if filters.date_from:
            q = q.filter(
                func.date(GameMatch.match_datetime) >= filters.date_from
            )

        if filters.date_to:
            q = q.filter(
                func.date(GameMatch.match_datetime) <= filters.date_to
            )

        total = q.count()
        matches = (
            q.order_by(GameMatch.match_datetime.desc())
             .offset((filters.page - 1) * filters.limit)
             .limit(filters.limit)
             .all()
        )

        data = [MatchOut.model_validate(m).model_dump(mode="json") for m in matches]
        total_pages = max(1, (total + filters.limit - 1) // filters.limit)
        meta = PaginationMeta(
            page=filters.page, limit=filters.limit, total=total,
            total_pages=total_pages,
            has_next=filters.page < total_pages,
            has_prev=filters.page > 1,
        ).model_dump()

        return jsonify({"data": data, "meta": meta}), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches/live
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/live", methods=["GET"])
def list_live_matches():
    """
    All matches with status='live', joined with home/away team names.

    Response 200:
        { "data": [MatchOut, …], "total": <int> }
    """
    db = get_db()
    try:
        matches = (
            db.query(GameMatch)
            .options(*_MATCH_LOAD)
            .filter(GameMatch.status == "live")
            .order_by(GameMatch.match_datetime.desc())
            .all()
        )

        data = [MatchOut.model_validate(m).model_dump(mode="json") for m in matches]
        return jsonify({"data": data, "total": len(data)}), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/matches/<id>
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/<int:match_id>", methods=["GET"])
def get_match(match_id: int):
    """
    Full match detail: teams, league, score, elapsed, venue,
    player_match_stat rows, and highlights.

    Response 200: MatchDetailOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        match = (
            db.query(GameMatch)
            .options(*_MATCH_DETAIL_LOAD)
            .filter(GameMatch.match_id == match_id)
            .first()
        )

        if match is None:
            return jsonify(
                ErrorOut(error=f"Match {match_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        return jsonify(MatchDetailOut.model_validate(match).model_dump(mode="json")), 200

    finally:
        db.close()


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
# GET /api/v1/matches/<id>/reviews
# ══════════════════════════════════════════════════════════════════════════════

@matches_bp.route("/<int:match_id>/reviews", methods=["GET"])
def get_match_reviews(match_id: int):
    """
    All reviews for a match plus AVG(rating).

    Response 200: ReviewWithStats
    Response 404: ErrorOut  (match not found)
    """
    db = get_db()
    try:
        match = db.query(GameMatch).filter(GameMatch.match_id == match_id).first()
        if match is None:
            return jsonify(
                ErrorOut(error=f"Match {match_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        reviews = (
            db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.match_id == match_id, Review.is_hidden == False)
            .order_by(Review.created_at.desc())
            .all()
        )

        agg = (
            db.query(func.avg(Review.rating), func.count(Review.review_id))
            .filter(Review.match_id == match_id, Review.is_hidden == False)
            .one()
        )
        avg_rating, total = agg
        avg_rating = round(float(avg_rating), 2) if avg_rating else None

        response = ReviewWithStats(
            average_rating=avg_rating,
            total_reviews=total,
            reviews=[ReviewOut.model_validate(r) for r in reviews],
        )

        return jsonify(response.model_dump(mode="json")), 200

    finally:
        db.close()


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

        # Check duplicate
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

        # Reload with user relationship
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