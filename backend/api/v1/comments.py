"""
comments.py  —  Flask Blueprint
──────────────────────────────────────────────────────────────────────────────
API routes for Comment and Review moderation resources.

Public endpoints:
    GET    /api/v1/comments                      – list comments (threaded)

Authenticated endpoints:
    POST   /api/v1/comments                      – post a comment
    PUT    /api/v1/comments/<id>                 – edit own comment (15-min window)
    DELETE /api/v1/comments/<id>                 – delete own comment (admin: any)

Admin-only endpoints:
    PATCH  /api/v1/admin/comments/<id>/hide      – hide a comment (is_hidden=true)
    PATCH  /api/v1/admin/reviews/<id>/hide       – hide a review  (is_hidden=true)
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import joinedload

from core.auth import require_auth, require_role
from database import SessionLocal
from model.model import Comment, Review
from model.schemas import (
    CommentCreate,
    CommentOut,
    CommentUpdate,
    ErrorOut,
    MessageOut,
    ReviewOut,
)

comments_bp = Blueprint("comments", __name__)

EDIT_WINDOW_MINUTES = 15


# ─── DB helper ────────────────────────────────────────────────────────────────

def get_db():
    return SessionLocal()


# ─── CHANGE 1: serialize_comment moved to top level so all routes can reuse it
# Handles all cases: replies=None, replies=list, replies=single ORM object ────

def serialize_comment(c):
    """Safely serialize a Comment ORM object handling None/non-list replies."""
    raw_replies = c.replies
    if raw_replies is None:
        replies = []
    elif isinstance(raw_replies, list):
        replies = raw_replies
    else:
        replies = [raw_replies]  # single ORM object — wrap in list

    result = CommentOut.model_validate(c).model_dump(mode="json")
    result["replies"] = [serialize_comment(r) for r in replies]
    return result


# ─── eager-load options ───────────────────────────────────────────────────────

_COMMENT_LOAD = [
    joinedload(Comment.user),
    #joinedload(Comment.replies).joinedload(Comment.user),
]


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/comments
# ══════════════════════════════════════════════════════════════════════════════

@comments_bp.route("", methods=["GET"])
def list_comments():
    """
    List comments for a match or player. Returns threaded replies.

    Required query params:
        ?entity_type=match|player
        ?entity_id=<int>

    Response 200:
        { "data": [CommentOut, …], "total": <int> }
    """
    db = get_db()
    try:
        entity_type = request.args.get("entity_type")
        entity_id   = request.args.get("entity_id")

        if not entity_type or entity_type not in ("match", "player"):
            return jsonify(
                ErrorOut(
                    error="entity_type is required and must be 'match' or 'player'.",
                    code="BAD_QUERY"
                ).model_dump()
            ), 400

        if not entity_id:
            return jsonify(
                ErrorOut(error="entity_id is required.", code="BAD_QUERY").model_dump()
            ), 400

        try:
            entity_id = int(entity_id)
        except ValueError:
            return jsonify(
                ErrorOut(error="entity_id must be an integer.", code="BAD_QUERY").model_dump()
            ), 400

        # Fetch only top-level comments (parent_id IS NULL); replies come nested
        # comments = (
        #     db.query(Comment)
        #     .options(*_COMMENT_LOAD)
        #     .filter(
        #         Comment.entity_type == entity_type,
        #         Comment.entity_id   == entity_id,
        #         Comment.parent_id   == None,
        #         Comment.is_hidden   == False,
        #     )
        #     .order_by(Comment.created_at.asc())
        #     .all()
        # )

        # CHANGE 2: use serialize_comment instead of direct model_validate
        #data = [serialize_comment(c) for c in comments]
        #return jsonify({"data": data, "total": len(data)}), 200

        comments = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(
                Comment.entity_type == entity_type,
                Comment.entity_id   == entity_id,
                Comment.parent_id   == None,
                Comment.is_hidden   == False,
            )
            .order_by(Comment.created_at.asc())
            .all()
        )

        # manually fetch replies for each top-level comment
        def fetch_replies(comment_id):
            replies = (
                db.query(Comment)
                .options(joinedload(Comment.user))
                .filter(
                    Comment.parent_id == comment_id,
                    Comment.is_hidden == False,
                )
                .order_by(Comment.created_at.asc())
                .all()
            )
            result = []
            for r in replies:
                r_dict = CommentOut.model_validate(r).model_dump(mode="json")
                r_dict["replies"] = fetch_replies(r.comment_id)  # recursive for deeper nesting
                result.append(r_dict)
            return result

        data = []
        for c in comments:
            c_dict = CommentOut.model_validate(c).model_dump(mode="json")
            c_dict["replies"] = fetch_replies(c.comment_id)
            data.append(c_dict)

        return jsonify({"data": data, "total": len(data)}), 200

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/comments
# ══════════════════════════════════════════════════════════════════════════════

@comments_bp.route("", methods=["POST"])
@require_auth
def post_comment():
    """
    Post a comment on a match or player.

    Request body:
        {
            "entity_type": "match" | "player",
            "entity_id":   <int>,
            "body":        "...",
            "parent_id":   <int>  (optional — supply to reply to a comment)
        }

    Response 201: CommentOut
    Response 404: ErrorOut  (parent_id not found)
    """
    db = get_db()
    try:
        try:
            payload = CommentCreate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 422

        user_id = g.user.get("sub")

        # Validate parent comment exists if supplied
        if payload.parent_id:
            parent = db.query(Comment).filter(Comment.comment_id == payload.parent_id).first()
            if parent is None:
                return jsonify(
                    ErrorOut(error=f"Parent comment {payload.parent_id} not found",
                             code="NOT_FOUND").model_dump()
                ), 404

        comment = Comment(
            user_id     = user_id,
            entity_type = payload.entity_type,
            entity_id   = payload.entity_id,
            body        = payload.body,
            parent_id   = payload.parent_id,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        # Reload with user relationship
        comment = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.comment_id == comment.comment_id)
            .first()
        )

        # CHANGE 3: use serialize_comment instead of direct model_validate
        return jsonify(serialize_comment(comment)), 201

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/v1/comments/<id>
# ══════════════════════════════════════════════════════════════════════════════

@comments_bp.route("/<int:comment_id>", methods=["PUT"])
@require_auth
def edit_comment(comment_id: int):
    """
    Edit own comment. Only allowed within 15 minutes of creation.

    Request body: { "body": "updated text" }

    Response 200: CommentOut
    Response 403: ErrorOut  (not owner, or edit window expired)
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        user_id = g.user.get("sub")

        comment = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.comment_id == comment_id)
            .first()
        )

        if comment is None:
            return jsonify(
                ErrorOut(error=f"Comment {comment_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        # Ownership check
        if str(comment.user_id) != str(user_id):
            return jsonify(
                ErrorOut(error="You can only edit your own comments.", code="FORBIDDEN").model_dump()
            ), 403

        # 15-minute edit window check
        now        = datetime.now(tz=timezone.utc)
        created_at = comment.created_at

        # Ensure timezone-aware for comparison
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if (now - created_at) > timedelta(minutes=EDIT_WINDOW_MINUTES):
            return jsonify(
                ErrorOut(
                    error="Edit window has expired. Comments can only be edited within 15 minutes.",
                    code="EDIT_WINDOW_EXPIRED"
                ).model_dump()
            ), 403

        try:
            payload = CommentUpdate.model_validate(request.get_json(force=True) or {})
        except ValidationError as exc:
            return jsonify(
                ErrorOut(error="Validation error", code="VALIDATION_ERROR",
                         details=exc.errors()).model_dump()
            ), 422

        comment.body      = payload.body
        comment.edited_at = now

        db.commit()
        db.refresh(comment)

        # CHANGE 4: use serialize_comment instead of direct model_validate
        return jsonify(serialize_comment(comment)), 200

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/comments/<id>
# ══════════════════════════════════════════════════════════════════════════════

@comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@require_auth
def delete_comment(comment_id: int):
    """
    Delete own comment. Admin can delete any comment regardless of ownership.

    Response 200: MessageOut
    Response 403: ErrorOut  (not owner and not admin)
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        user_id   = g.user.get("sub")
        user_role = g.user.get("role")

        comment = db.query(Comment).filter(Comment.comment_id == comment_id).first()

        if comment is None:
            return jsonify(
                ErrorOut(error=f"Comment {comment_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        # Admin can delete any; others can only delete own
        if user_role != "admin" and str(comment.user_id) != str(user_id):
            return jsonify(
                ErrorOut(error="You can only delete your own comments.", code="FORBIDDEN").model_dump()
            ), 403

        db.delete(comment)
        db.commit()

        return jsonify(MessageOut(message=f"Comment {comment_id} deleted.").model_dump()), 200

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# PATCH /api/v1/admin/comments/<id>/hide
# ══════════════════════════════════════════════════════════════════════════════

@comments_bp.route("/admin/comments/<int:comment_id>/hide", methods=["PATCH"])
@require_auth
@require_role(["admin"])
def hide_comment(comment_id: int):
    """
    Admin sets is_hidden=true on a comment.
    Comment stays in DB but is filtered from public reads.

    Response 200: CommentOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        comment = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.comment_id == comment_id)
            .first()
        )

        if comment is None:
            return jsonify(
                ErrorOut(error=f"Comment {comment_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        comment.is_hidden = True
        db.commit()
        db.refresh(comment)

        # CHANGE 5: use serialize_comment instead of direct model_validate
        return jsonify(serialize_comment(comment)), 200

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# PATCH /api/v1/admin/reviews/<id>/hide
# ══════════════════════════════════════════════════════════════════════════════

@comments_bp.route("/admin/reviews/<int:review_id>/hide", methods=["PATCH"])
@require_auth
@require_role(["admin"])
def hide_review(review_id: int):
    """
    Admin sets is_hidden=true on a review.
    Review stays in DB but is filtered from public reads.

    Response 200: ReviewOut
    Response 404: ErrorOut
    """
    db = get_db()
    try:
        review = (
            db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.review_id == review_id)
            .first()
        )

        if review is None:
            return jsonify(
                ErrorOut(error=f"Review {review_id} not found", code="NOT_FOUND").model_dump()
            ), 404

        review.is_hidden = True
        db.commit()
        db.refresh(review)

        # no replies field on Review — direct model_validate is safe here
        return jsonify(ReviewOut.model_validate(review).model_dump(mode="json")), 200

    except Exception as err:
        db.rollback()
        return jsonify(ErrorOut(error=str(err)).model_dump()), 500

    finally:
        db.close()