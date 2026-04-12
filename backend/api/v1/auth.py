import re
from typing import Dict, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request

from model.model import supabase_signup

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def success(data, status=200):
	return jsonify({"ok": True, "data": data, "error": None}), status


def failure(code: str, message: str, status: int, details=None):
	err = {"code": code, "message": message}
	if details is not None:
		err["details"] = details
	return jsonify({"ok": False, "data": None, "error": err}), status


def validate_signup_payload(payload) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
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


@auth_bp.post("/signup")
def signup():
	payload = request.get_json(silent=True)
	validation_error, validated = validate_signup_payload(payload)

	if validation_error or validated is None:
		return failure("VALIDATION_ERROR", validation_error or "Validation failed.", 400, validated)

	result = supabase_signup(
		current_app.config.get("SUPABASE_URL", ""),
		current_app.config.get("SUPABASE_ANON_KEY", ""),
		validated["email"],
		validated["password"],
		validated["display_name"],
	)

	if result.get("ok"):
		return success(result["data"], result.get("status", 201))

	return failure(
		result.get("error_code", "SUPABASE_AUTH_ERROR"),
		result.get("error_message", "Signup failed."),
		result.get("status", 502),
	)
