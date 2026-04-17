from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from datetime import datetime, timezone

# Database and Models
from database import SessionLocal
import model.model as models

# Pydantic Schemas
from model.schemas import ProfileOut,AdminRoleUpdate

# Authentication Core
from core.auth import  require_auth, require_role

# Create the Blueprint
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def get_db():
    """Get database session."""
    return SessionLocal()



@admin_bp.route("/admin/users/<user_id>/role", methods=["PUT"])
@require_auth
@require_role(["admin"])
def update_user_role(user_id):
    """
    Admin endpoint: Update a user's role and team_managed.
    Requires admin role.
    
    Request body:
        {
            "role": "team_manager",
            "team_managed": 5
        }
    
    Response: 200 OK
        {
            "id": "uuid",
            "email": "user@example.com",
            "display_name": "Manager",
            "role": "team_manager",
            "team_managed": 5,
            "is_active": true
        }
    """
    db = get_db()
    try:
        # Fetch target profile
        profile = db.query(models.Profile).filter(
            models.Profile.id == user_id
        ).first()
        
        if not profile:
            return jsonify({
                "error": "User not found",
                "code": "USER_NOT_FOUND"
            }), 404
        
        # Validate role update
        json_data = request.get_json() or {}
        role_update = AdminRoleUpdate(**json_data)
        
        # Apply updates
        profile.role = role_update.role
        profile.team_managed = role_update.team_managed
        profile.updated_at = datetime.now(tz=timezone.utc)
        
        db.commit()
        db.refresh(profile)
        
        return jsonify(ProfileOut.model_validate(profile).model_dump()), 200
        
    except ValidationError as err:
        db.rollback()
        return jsonify({
            "error": "Validation error",
            "details": err.errors()
        }), 422
    except Exception as err:
        db.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        db.close()