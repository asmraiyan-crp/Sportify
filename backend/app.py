import os

from flask import Flask

from api.v1.auth import auth_bp


def create_app() -> Flask:
	app = Flask(__name__)

	app.config["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "").rstrip("/")
	app.config["SUPABASE_ANON_KEY"] = os.getenv("SUPABASE_ANON_KEY", "")

	app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

	return app


app = create_app()


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
