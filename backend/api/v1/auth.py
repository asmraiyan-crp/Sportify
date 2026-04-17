"""
Authentication module with JWT tokens and password hashing.
Handles user registration, login, token generation, and validation.
"""

import re
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from uuid import UUID

import jwt
import bcrypt
from flask import Blueprint, jsonify, request
from functools import wraps

from database import get_session
from model.model import Profile

auth_bp = Blueprint("auth", __name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITY FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def success(data, status=200):
	"""Return success response."""
	return jsonify({"ok": True, "data": data, "error": None}), status


def failure(code: str, message: str, status: int, details=None):
	"""Return error response."""
	err = {"code": code, "message": message}
	if details is not None:
		err["details"] = details
	return jsonify({"ok": False, "data": None, "error": err}), status


def hash_password(password: str) -> str:
	"""Hash password using bcrypt."""
	salt = bcrypt.gensalt()
	return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
	"""Verify password against hash."""
	try:
		return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
	except Exception:
		return False


def create_access_token(user_id: UUID, expires_in_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
	"""Create JWT access token."""
	payload = {
		'sub': str(user_id),
		'type': 'access',
		'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes),
		'iat': datetime.utcnow()
	}
	return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID, expires_in_days: int = REFRESH_TOKEN_EXPIRE_DAYS) -> str:
	"""Create JWT refresh token."""
	payload = {
		'sub': str(user_id),
		'type': 'refresh',
		'exp': datetime.utcnow() + timedelta(days=expires_in_days),
		'iat': datetime.utcnow()
	}
	return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
	"""Verify JWT token and return decoded payload."""
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		return True, payload, None
	except jwt.ExpiredSignatureError:
		return False, None, "Token has expired"
	except jwt.InvalidTokenError as e:
		return False, None, f"Invalid token: {str(e)}"


def extract_user_id_from_token(token: str) -> Tuple[bool, Optional[UUID], Optional[str]]:
	"""Extract user_id from token."""
	valid, payload, error = verify_token(token)
	if not valid:
		return False, None, error
	
	try:
		user_id = UUID(payload.get('sub'))
		return True, user_id, None
	except (ValueError, TypeError):
		return False, None, "Invalid user_id in token"


def token_required(f):
	"""Decorator to protect routes that require authentication."""
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None
		
		# Check Authorization header
		if 'Authorization' in request.headers:
			auth_header = request.headers['Authorization']
			try:
				token = auth_header.split(' ')[1]  # Bearer <token>
			except IndexError:
				return failure("INVALID_TOKEN", "Invalid authorization header", 401)
		
		if not token:
			return failure("MISSING_TOKEN", "Authorization token is required", 401)
		
		valid, user_id, error = extract_user_id_from_token(token)
		if not valid:
			return failure("INVALID_TOKEN", error or "Invalid token", 401)
		
		# Store user_id in request context
		request.user_id = user_id
		return f(*args, **kwargs)
	
	return decorated


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VALIDATION FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def validate_signup_payload(payload) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
	"""Validate signup request payload."""
	if not isinstance(payload, dict):
		return "Body must be a JSON object.", None

	email = str(payload.get("email", "")).strip()
	password = str(payload.get("password", ""))
	display_name = str(payload.get("display_name", "")).strip()

	errors = {}
	if not email:
		errors["email"] = "Email is required."
	elif not EMAIL_RE.match(email):
		errors["email"] = "Email format is invalid."

	if not password:
		errors["password"] = "Password is required."
	elif len(password) < 8:
		errors["password"] = "Password must be at least 8 characters."

	if not display_name:
		errors["display_name"] = "Display name is required."
	elif len(display_name) < 2 or len(display_name) > 50:
		errors["display_name"] = "Display name must be between 2 and 50 characters."

	if errors:
		return "Validation failed.", errors

	return None, {"email": email, "password": password, "display_name": display_name}


def validate_login_payload(payload) -> Tuple[Optional[str], Optional[Dict]]:
	"""Validate login request payload."""
	if not isinstance(payload, dict):
		return "Body must be a JSON object.", None

	email = str(payload.get("email", "")).strip()
	password = str(payload.get("password", ""))

	errors = {}
	if not email:
		errors["email"] = "Email is required."
	elif not EMAIL_RE.match(email):
		errors["email"] = "Email format is invalid."

	if not password:
		errors["password"] = "Password is required."

	if errors:
		return "Validation failed.", errors

	return None, {"email": email, "password": password}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@auth_bp.post("/signup")
def signup():
	"""
	User signup endpoint - creates a new user profile with hashed password.
	
	Request body:
	{
		"email": "user@example.com",
		"password": "securepassword123",
		"display_name": "John Doe"
	}
	
	Response:
	{
		"ok": true,
		"data": {
			"user_id": "uuid",
			"email": "user@example.com",
			"display_name": "John Doe",
			"role": "fan",
			"access_token": "jwt_token",
			"refresh_token": "jwt_token",
			"token_type": "Bearer"
		}
	}
	"""
	payload = request.get_json(silent=True)
	validation_error, validated = validate_signup_payload(payload)

	if validation_error or validated is None:
		return failure("VALIDATION_ERROR", validation_error or "Validation failed.", 400, validated)

	db = None
	try:
		db = get_session()
		
		# Check if email already exists
		existing_user = db.query(Profile).filter(Profile.email == validated["email"]).first()
		if existing_user:
			return failure(
				"EMAIL_ALREADY_EXISTS",
				"This email is already registered.",
				409
			)
		
		# Hash password
		hashed_password = hash_password(validated["password"])
		
		# Create new user profile
		new_user = Profile(
			email=validated["email"],
			password_hash=hashed_password,
			display_name=validated["display_name"],
			role="fan",  # Default role
			is_active=True
		)
		
		db.add(new_user)
		db.commit()
		db.refresh(new_user)
		
		# Generate tokens
		access_token = create_access_token(new_user.id)
		refresh_token = create_refresh_token(new_user.id)
		
		user_data = {
			"user_id": str(new_user.id),
			"email": new_user.email,
			"display_name": new_user.display_name,
			"role": new_user.role,
			"access_token": access_token,
			"refresh_token": refresh_token,
			"token_type": "Bearer",
			"expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # In seconds
		}
		
		return success(user_data, 201)
		
	except Exception as e:
		return failure(
			"SIGNUP_ERROR",
			f"Failed to create user: {str(e)}",
			500
		)
	finally:
		if db:
			db.close()


@auth_bp.post("/login")
def login():
	"""
	User login endpoint - validates email/password and returns JWT tokens.
	
	Request body:
	{
		"email": "user@example.com",
		"password": "securepassword123"
	}
	
	Response:
	{
		"ok": true,
		"data": {
			"user_id": "uuid",
			"email": "user@example.com",
			"display_name": "John Doe",
			"role": "fan",
			"access_token": "jwt_token",
			"refresh_token": "jwt_token",
			"token_type": "Bearer"
		}
	}
	"""
	payload = request.get_json(silent=True)
	validation_error, validated = validate_login_payload(payload)
	
	if validation_error or validated is None:
		return failure("VALIDATION_ERROR", validation_error or "Validation failed.", 400, validated)
	
	db = None
	try:
		db = get_session()
		
		user = db.query(Profile).filter(Profile.email == validated["email"]).first()
		
		if not user:
			return failure("INVALID_CREDENTIALS", "Invalid email or password.", 401)
		
		if not user.is_active:
			return failure("ACCOUNT_INACTIVE", "This account has been deactivated.", 403)
		
		# Verify password
		if not user.password_hash or not verify_password(validated["password"], user.password_hash):
			return failure("INVALID_CREDENTIALS", "Invalid email or password.", 401)
		
		# Generate tokens
		access_token = create_access_token(user.id)
		refresh_token = create_refresh_token(user.id)
		
		user_data = {
			"user_id": str(user.id),
			"email": user.email,
			"display_name": user.display_name,
			"role": user.role,
			"access_token": access_token,
			"refresh_token": refresh_token,
			"token_type": "Bearer",
			"expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # In seconds
		}
		
		return success(user_data, 200)
		
	except Exception as e:
		return failure("LOGIN_ERROR", f"Login failed: {str(e)}", 500)
	finally:
		if db:
			db.close()


@auth_bp.post("/refresh")
def refresh():
	"""
	Refresh access token using a valid refresh token.
	
	Request body:
	{
		"refresh_token": "refresh_jwt_token"
	}
	
	Response:
	{
		"ok": true,
		"data": {
			"access_token": "new_jwt_token",
			"token_type": "Bearer",
			"expires_in": 1800
		}
	}
	"""
	payload = request.get_json(silent=True)
	
	if not isinstance(payload, dict) or not payload.get("refresh_token"):
		return failure("MISSING_TOKEN", "Refresh token is required.", 400)
	
	refresh_token = payload.get("refresh_token")
	
	valid, token_payload, error = verify_token(refresh_token)
	if not valid or token_payload.get('type') != 'refresh':
		return failure("INVALID_TOKEN", error or "Invalid refresh token", 401)
	
	try:
		user_id = UUID(token_payload.get('sub'))
		new_access_token = create_access_token(user_id)
		
		data = {
			"access_token": new_access_token,
			"token_type": "Bearer",
			"expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
		}
		
		return success(data, 200)
		
	except Exception as e:
		return failure("TOKEN_ERROR", f"Failed to refresh token: {str(e)}", 500)


@auth_bp.post("/logout")
@token_required
def logout():
	"""
	Logout endpoint - invalidates the current session.
	In a real app, you'd add the token to a blacklist.
	
	Response:
	{
		"ok": true,
		"data": {
			"message": "Successfully logged out"
		}
	}
	"""
	return success({"message": "Successfully logged out"}, 200)


@auth_bp.get("/me")
@token_required
def get_current_user():
	"""
	Get current authenticated user's profile.
	
	Response:
	{
		"ok": true,
		"data": {
			"user_id": "uuid",
			"email": "user@example.com",
			"display_name": "John Doe",
			"role": "fan",
			"is_active": true
		}
	}
	"""
	db = None
	try:
		db = get_session()
		user = db.query(Profile).filter(Profile.id == request.user_id).first()
		
		if not user:
			return failure("USER_NOT_FOUND", "User profile not found", 404)
		
		user_data = {
			"user_id": str(user.id),
			"email": user.email,
			"display_name": user.display_name,
			"role": user.role,
			"is_active": user.is_active,
			"created_at": user.created_at.isoformat() if user.created_at else None
		}
		
		return success(user_data, 200)
		
	except Exception as e:
		return failure("PROFILE_ERROR", f"Failed to fetch profile: {str(e)}", 500)
	finally:
		if db:
			db.close()


@auth_bp.put("/me")
@token_required
def update_current_user():
	"""
	Update current user's profile.
	
	Request body:
	{
		"display_name": "New Name",
		"role": "team_manager"  (admin only)
	}
	
	Response:
	{
		"ok": true,
		"data": {
			"user_id": "uuid",
			"email": "user@example.com",
			"display_name": "New Name",
			"role": "team_manager"
		}
	}
	"""
	payload = request.get_json(silent=True)
	
	if not isinstance(payload, dict):
		return failure("INVALID_REQUEST", "Body must be a JSON object.", 400)
	
	db = None
	try:
		db = get_session()
		user = db.query(Profile).filter(Profile.id == request.user_id).first()
		
		if not user:
			return failure("USER_NOT_FOUND", "User profile not found", 404)
		
		# Update display_name if provided
		if "display_name" in payload:
			new_name = str(payload.get("display_name", "")).strip()
			if new_name and 2 <= len(new_name) <= 50:
				user.display_name = new_name
		
		# Only admins can change role
		if "role" in payload:
			if user.role != 'admin':
				return failure("FORBIDDEN", "Only admins can change roles", 403)
			new_role = str(payload.get("role", "")).strip()
			if new_role in ('admin', 'team_manager', 'fan'):
				user.role = new_role
		
		user.updated_at = datetime.utcnow()
		db.commit()
		db.refresh(user)
		
		user_data = {
			"user_id": str(user.id),
			"email": user.email,
			"display_name": user.display_name,
			"role": user.role
		}
		
		return success(user_data, 200)
		
	except Exception as e:
		return failure("UPDATE_ERROR", f"Failed to update profile: {str(e)}", 500)
	finally:
		if db:
			db.close()
