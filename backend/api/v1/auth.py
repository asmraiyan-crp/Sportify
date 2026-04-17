"""
auth.py – Authentication endpoints for Sportify.

Handles:
  • POST /auth/register – Register new user
  • POST /auth/login – Login with email/password
  • POST /auth/logout – Logout (clear session)
  • POST /auth/password-reset – Request password reset email
  • POST /auth/password-reset/confirm – Confirm password reset with token
  • GET /users/me – Get current user profile (requires auth)
  • PUT /users/me – Update current user profile (requires auth)

Uses JWT tokens stored in httpOnly cookies.
Manual password hashing (bcrypt) — no Supabase Auth.
"""

from flask import Blueprint, request, jsonify, make_response, g
from passlib.context import CryptContext
from pydantic import ValidationError
from datetime import datetime, timezone
from uuid import uuid4

# Database and Models
from database import SessionLocal
import model.model as models

# Pydantic Schemas
from model.schemas import (
    RegisterCreate,
    LoginCreate,
    TokenOut,
    ProfileOut,
    ProfileUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    AdminRoleUpdate,
)

# Authentication Core
from core.auth import create_access_token, require_auth, require_role

# Create the Blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    """Get database session."""
    return SessionLocal()


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "display_name": "John Doe"  (optional)
        }
    
    Response: 201 Created
        {
            "id": "uuid",
            "email": "user@example.com",
            "display_name": "John Doe",
            "role": "fan",
            "is_active": true
        }
    """
    db = get_db()
    try:
        # 1. Validate with Pydantic
        json_data = request.get_json() or {}
        user_data = RegisterCreate(**json_data)
        
        # 2. Check if email already exists
        existing = db.query(models.Profile).filter(
            models.Profile.email == user_data.email
        ).first()
        if existing:
            return jsonify({
                "error": "Email already registered.",
                "code": "EMAIL_EXISTS"
            }), 409
        
        # 3. Hash password
        hashed_password = pwd_context.hash(user_data.password)
        
        # 4. Create new profile
        new_profile = models.Profile(
            id=uuid4(),
            email=user_data.email,
            password_hash=hashed_password,
            display_name=user_data.display_name,
            role="fan",  # Default role
            is_active=True,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        # 5. Return profile as per ProfileOut schema
        return jsonify(ProfileOut.model_validate(new_profile).model_dump()), 201
        
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


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login with email and password.
    
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }
    
    Response: 200 OK
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "token_type": "Bearer",
            "expires_in": 1800,
            "user": {
                "id": "uuid",
                "email": "user@example.com",
                "display_name": "John Doe",
                "role": "fan",
                "is_active": true
            }
        }
    
    Sets httpOnly cookie with access_token.
    """
    db = get_db()
    try:
        # 1. Validate request
        json_data = request.get_json() or {}
        login_data = LoginCreate(**json_data)
        
        # 2. Find user by email
        profile = db.query(models.Profile).filter(
            models.Profile.email == login_data.email
        ).first()
        
        if not profile:
            return jsonify({
                "error": "Invalid credentials",
                "code": "INVALID_CREDENTIALS"
            }), 401
        
        # 3. Verify password
        if not pwd_context.verify(login_data.password, profile.password_hash):
            return jsonify({
                "error": "Invalid credentials",
                "code": "INVALID_CREDENTIALS"
            }), 401
        
        # 4. Check if profile is active
        if not profile.is_active:
            return jsonify({
                "error": "Account is not active",
                "code": "ACCOUNT_INACTIVE"
            }), 403
        
        # 5. Generate token (expires in ~30 mins by default)
        token_data = {
            "sub": str(profile.id),
            "email": profile.email,
            "role": profile.role,
        }
        access_token = create_access_token(token_data)
        
        # 6. Prepare response (following TokenOut schema)
        from core.auth import EXPIRY_MINUTE
        response_data = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": EXPIRY_MINUTE * 60,  # Convert minutes to seconds
            "user": ProfileOut.model_validate(profile).model_dump()
        }
        
        # 7. Create response with httpOnly cookie
        response = make_response(jsonify(response_data), 200)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,  # MUST be True in production (HTTPS)
            samesite="Lax",
            max_age=EXPIRY_MINUTE * 60
        )
        
        return response
        
    except ValidationError as err:
        return jsonify({
            "error": "Validation error",
            "details": err.errors()
        }), 422
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    """
    Logout the current user.
    Clears the httpOnly access_token cookie.
    
    Response: 200 OK
        {"message": "Logged out successfully"}
    """
    response = make_response(jsonify({"message": "Logged out successfully"}), 200)
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="Lax"
    )
    return response


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RESET REQUEST
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/password-reset", methods=["POST"])
def password_reset_request():
    """
    Request password reset email.
    
    Request body:
        {
            "email": "user@example.com"
        }
    
    Response: 200 OK
        {"message": "Password reset email sent"}
    
    Note: This is a placeholder. Real implementation should:
      • Generate a token
      • Store reset token in DB with expiry
      • Send email with reset link
    """
    db = get_db()
    try:
        json_data = request.get_json() or {}
        reset_req = PasswordResetRequest(**json_data)
        
        # Check if profile exists
        profile = db.query(models.Profile).filter(
            models.Profile.email == reset_req.email
        ).first()
        
        if not profile:
            # For security, don't reveal if email exists
            return jsonify({"message": "Password reset email sent"}), 200
        
        # TODO: Generate reset token and send email
        # For now, just return success
        
        return jsonify({"message": "Password reset email sent"}), 200
        
    except ValidationError as err:
        return jsonify({
            "error": "Validation error",
            "details": err.errors()
        }), 422
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD RESET CONFIRM
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/password-reset/confirm", methods=["POST"])
def password_reset_confirm():
    """
    Confirm password reset with token.
    
    Request body:
        {
            "token": "reset_token_from_email",
            "new_password": "NewSecurePass123"
        }
    
    Response: 200 OK
        {"message": "Password reset successfully"}
    
    Note: This is a placeholder. Real implementation should:
      • Validate the reset token
      • Check token expiry
      • Update password_hash
    """
    db = get_db()
    try:
        json_data = request.get_json() or {}
        reset_confirm = PasswordResetConfirm(**json_data)
        
        # TODO: Validate reset token from DB
        # For now, return success
        
        return jsonify({"message": "Password reset successfully"}), 200
        
    except ValidationError as err:
        return jsonify({
            "error": "Validation error",
            "details": err.errors()
        }), 422
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# GET CURRENT USER
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """
    Get current authenticated user profile.
    
    Response: 200 OK
        {
            "id": "uuid",
            "email": "user@example.com",
            "display_name": "John Doe",
            "role": "fan",
            "team_managed": null,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    """
    db = get_db()
    try:
        # Get user_id from JWT payload (stored in g.user by @require_auth)
        user_id = g.user.get("sub")
        
        # Fetch profile from DB
        profile = db.query(models.Profile).filter(
            models.Profile.id == user_id
        ).first()
        
        if not profile:
            return jsonify({
                "error": "User not found",
                "code": "USER_NOT_FOUND"
            }), 404
        
        return jsonify(ProfileOut.model_validate(profile).model_dump()), 200
        
    except Exception as err:
        return jsonify({"error": str(err)}), 500
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE CURRENT USER
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["PUT"])
@require_auth
def update_current_user():
    """
    Update current user profile.
    
    Request body (all optional):
        {
            "display_name": "New Name"
        }
    
    Response: 200 OK
        {
            "id": "uuid",
            "email": "user@example.com",
            "display_name": "New Name",
            "role": "fan",
            "team_managed": null,
            "is_active": true
        }
    """
    db = get_db()
    try:
        # Get user_id from JWT
        user_id = g.user.get("sub")
        
        # Fetch profile
        profile = db.query(models.Profile).filter(
            models.Profile.id == user_id
        ).first()
        
        if not profile:
            return jsonify({
                "error": "User not found",
                "code": "USER_NOT_FOUND"
            }), 404
        
        # Validate update data
        json_data = request.get_json() or {}
        update_data = ProfileUpdate(**json_data)
        
        # Apply updates
        if update_data.display_name is not None:
            profile.display_name = update_data.display_name
        
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