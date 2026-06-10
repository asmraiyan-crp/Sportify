from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor

# Database and Models
from database import SessionLocal, get_db as get_psycopg_db
import model.model as models

# Pydantic Schemas
from model.schemas import ProfileOut, AdminRoleUpdate

# Authentication Core
from core.auth import require_auth, require_role

# Create the Blueprint
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def get_db():
    """Get database session."""
    return SessionLocal()

@admin_bp.route("/users", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_users():
    """Admin endpoint: Get all users with pagination."""
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    offset = (page - 1) * limit
    
    try:
        with get_psycopg_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, email, display_name, role, team_managed, is_active, created_at
                    FROM profiles
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                users = cur.fetchall()
                
                cur.execute("SELECT count(*) as total FROM profiles")
                total = cur.fetchone()['total']
                
        return jsonify({
            "users": users,
            "total": total,
            "page": page,
            "limit": limit
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/users/<user_id>/role", methods=["PUT"])
@require_auth
@require_role(["admin"])
def update_user_role(user_id):
    """
    Admin endpoint: Update a user's role and team_managed.
    Requires admin role.
    """
    db = get_db()
    try:
        profile = db.query(models.Profile).filter(models.Profile.id == user_id).first()
        if not profile:
            return jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 404
        
        json_data = request.get_json() or {}
        role_update = AdminRoleUpdate(**json_data)
        
        profile.role = role_update.role
        profile.team_managed = role_update.team_managed
        profile.updated_at = datetime.now(tz=timezone.utc)
        
        db.commit()
        db.refresh(profile)
        
        return jsonify(ProfileOut.model_validate(profile).model_dump()), 200
    except ValidationError as err:
        db.rollback()
        return jsonify({"error": "Validation error", "details": err.errors()}), 422
    except Exception as err:
        db.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        db.close()

@admin_bp.route("/reviews", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_reviews():
    try:
        with get_psycopg_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        r.review_id,
                        r.match_id,
                        r.user_id,
                        r.rating,
                        r.body,
                        r.is_hidden,
                        r.created_at,
                        p.display_name,
                        COALESCE(ht.name, 'Team ' || m.home_team_id::text)
                            || ' vs '
                            || COALESCE(at.name, 'Team ' || m.away_team_id::text)
                            AS match_title
                    FROM review r
                    JOIN profiles p ON r.user_id = p.id
                    JOIN game_match m ON r.match_id = m.match_id
                    LEFT JOIN team ht ON ht.team_id = m.home_team_id
                    LEFT JOIN team at ON at.team_id = m.away_team_id
                    ORDER BY r.created_at DESC
                """)
                reviews = [dict(row) for row in cur.fetchall()]
        return jsonify({"reviews": reviews}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/comments", methods=["GET"])
@require_auth
@require_role(["admin"])
def get_comments():
    try:
        with get_psycopg_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT c.comment_id, c.user_id, c.entity_type, c.entity_id, c.body, c.is_hidden, c.created_at,
                           p.display_name
                    FROM comment c
                    JOIN profiles p ON c.user_id = p.id
                    ORDER BY c.created_at DESC
                """)
                comments = cur.fetchall()
        return jsonify({"comments": comments}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/reviews/<int:review_id>/hide", methods=["PATCH"])
@require_auth
@require_role(["admin"])
def hide_review(review_id):
    try:
        data = request.get_json() or {}
        is_hidden = data.get("is_hidden", True)
        
        with get_psycopg_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE review
                    SET is_hidden = %s
                    WHERE review_id = %s
                    RETURNING *
                """, (is_hidden, review_id))
                updated = cur.fetchone()
                conn.commit()
                if not updated:
                    return jsonify({"error": "Review not found"}), 404
        return jsonify(updated), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/comments/<int:comment_id>/hide", methods=["PATCH"])
@require_auth
@require_role(["admin"])
def hide_comment(comment_id):
    try:
        data = request.get_json() or {}
        is_hidden = data.get("is_hidden", True)
        
        with get_psycopg_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE comment
                    SET is_hidden = %s
                    WHERE comment_id = %s
                    RETURNING *
                """, (is_hidden, comment_id))
                updated = cur.fetchone()
                conn.commit()
                if not updated:
                    return jsonify({"error": "Comment not found"}), 404
        return jsonify(updated), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

