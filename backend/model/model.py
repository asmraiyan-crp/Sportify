import json
from typing import Any, Dict
from urllib import error, request


def supabase_signup(supabase_url: str, anon_key: str, email: str, password: str, display_name: str) -> Dict[str, Any]:
	if not supabase_url or not anon_key:
		return {
			"ok": False,
			"status": 500,
			"error_code": "BACKEND_CONFIG_ERROR",
			"error_message": "Supabase is not configured on the server.",
		}

	url = f"{supabase_url}/auth/v1/signup"
	payload = {
		"email": email,
		"password": password,
		"data": {"display_name": display_name},
	}

	body = json.dumps(payload).encode("utf-8")
	headers = {
		"Content-Type": "application/json",
		"apikey": anon_key,
	}
	req = request.Request(url=url, data=body, headers=headers, method="POST")

	try:
		with request.urlopen(req, timeout=15) as res:
			raw = res.read().decode("utf-8") or "{}"
			parsed = json.loads(raw)

			user = parsed.get("user") or {}
			identities = user.get("identities")
			email_verification_required = bool(identities)

			return {
				"ok": True,
				"status": 201,
				"data": {
					"user_id": user.get("id"),
					"email": user.get("email", email),
					"email_verification_required": email_verification_required,
				},
			}

	except error.HTTPError as exc:
		raw_err = exc.read().decode("utf-8") if exc.fp else ""
		parsed_err: Dict[str, Any] = {}
		if raw_err:
			try:
				parsed_err = json.loads(raw_err)
			except json.JSONDecodeError:
				parsed_err = {}

		message = parsed_err.get("msg") or parsed_err.get("error_description") or parsed_err.get("message") or "Signup failed."
		message_lower = str(message).lower()

		if "already" in message_lower and "register" in message_lower:
			return {
				"ok": False,
				"status": 409,
				"error_code": "EMAIL_ALREADY_EXISTS",
				"error_message": "This email is already registered.",
			}

		if exc.code == 400:
			return {
				"ok": False,
				"status": 400,
				"error_code": "SUPABASE_AUTH_ERROR",
				"error_message": "Signup request was rejected by Supabase.",
			}

		return {
			"ok": False,
			"status": 502,
			"error_code": "SUPABASE_AUTH_ERROR",
			"error_message": "Failed to reach Supabase auth service.",
		}

	except Exception:
		return {
			"ok": False,
			"status": 502,
			"error_code": "SUPABASE_AUTH_ERROR",
			"error_message": "Failed to reach Supabase auth service.",
		}
