"""Test API endpoints to verify database connectivity and model structure."""

from flask import Blueprint, jsonify
from sqlalchemy.exc import OperationalError

test_bp = Blueprint("test", __name__)


@test_bp.get("/health")
def health_check():
	"""Health check endpoint - always returns OK."""
	return jsonify({
		"ok": True,
		"status": "Backend is running",
	}), 200


@test_bp.get("/db-test")
def database_test():
	"""Test database connectivity by querying sports."""
	try:
		from database import get_session
		from model.model import Sport
		
		db = get_session()
		
		# Try to query all sports from the database
		sports = db.query(Sport).limit(10).all()
		
		# Convert to dict for JSON serialization
		sports_data = [
			{
				"sport_id": sport.sport_id,
				"name": sport.name,
				"description": sport.description,
				"created_at": sport.created_at.isoformat() if sport.created_at else None
			}
			for sport in sports
		]
		
		db.close()
		
		return jsonify({
			"ok": True,
			"message": "Database connection successful",
			"data": {
				"sports_count": len(sports_data),
				"sports": sports_data
			}
		}), 200
		
	except OperationalError as e:
		return jsonify({
			"ok": False,
			"message": "Database connection failed",
			"error": "Could not connect to database. Ensure PostgreSQL is running and DATABASE_URL is configured.",
			"details": str(e)
		}), 503
		
	except Exception as e:
		return jsonify({
			"ok": False,
			"message": "Database error",
			"error": str(e)
		}), 500


@test_bp.get("/models-info")
def models_info():
	"""Get information about available models."""
	try:
		from model.model import Base
		from sqlalchemy.inspection import inspect
		
		models_info = []
		
		# Get all mapped classes
		mappers = Base.registry.mappers
		for mapper in mappers:
			cls = mapper.class_
			table_name = cls.__tablename__
			
			# Count columns and relationships
			columns = list(inspect(cls).columns)
			relationships = list(inspect(cls).relationships)
			
			models_info.append({
				"class_name": cls.__name__,
				"table_name": table_name,
				"columns_count": len(columns),
				"relationships_count": len(relationships)
			})
		
		return jsonify({
			"ok": True,
			"message": "Available models",
			"data": {
				"total_models": len(models_info),
				"models": sorted(models_info, key=lambda x: x["class_name"])
			}
		}), 200
		
	except Exception as e:
		return jsonify({
			"ok": False,
			"message": "Error retrieving models",
			"error": str(e)
		}), 500


@test_bp.get("/db-init")
def database_init():
	"""Initialize database tables."""
	try:
		from database import init_db
		
		init_db()
		
		return jsonify({
			"ok": True,
			"message": "Database tables initialized successfully"
		}), 200
		
	except Exception as e:
		return jsonify({
			"ok": False,
			"message": "Failed to initialize database",
			"error": str(e)
		}), 500


@test_bp.get("/status")
def status():
	"""Get backend status and configuration."""
	import os
	from database import DATABASE_URL
	from model.model import Base
	
	db_url = str(DATABASE_URL)
	# Hide password in logs
	if "://" in db_url:
		parts = db_url.split("://")
		if "@" in parts[1]:
			user_pass, host = parts[1].split("@")
			db_url = f"{parts[0]}://***:***@{host}"
	
	return jsonify({
		"ok": True,
		"status": {
			"environment": os.getenv("FLASK_ENV", "production"),
			"database_url": db_url,
			"models_count": len(Base.registry.mappers),
			"debug_mode": os.getenv("FLASK_DEBUG", "False").lower() == "true"
		}
	}), 200

