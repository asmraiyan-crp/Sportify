import os
from api.v1.leagues import leagues_bp
from flask import Flask
from api.v1.admin import admin_bp
from api.v1.auth import auth_bp
from api.v1.testapi import test_bp
from api.v1.follow import me_bp, follow_bp

def create_app() -> Flask:
	app = Flask(__name__)

	# Register blueprints
	app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
	app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
	app.register_blueprint(test_bp, url_prefix="/api/v1/test")
	app.register_blueprint(leagues_bp, url_prefix="/api/v1/leagues")
	app.register_blueprint(me_bp,     url_prefix="/api/v1/users")
	app.register_blueprint(follow_bp, url_prefix="/api/v1/follow")
	# Initialize database (create tables if they don't exist)
	try:
		from database import init_db
		with app.app_context():
			init_db()
	except Exception as e:
		print(f"Warning: Could not initialize database: {e}")

	return app


app = create_app()


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
