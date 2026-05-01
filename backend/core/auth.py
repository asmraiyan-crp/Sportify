import os
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import uuid4
from flask import request, jsonify, g
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv 


logger = logging.getLogger(__name__)
load_dotenv()

EXPIRY_MINUTE = int(os.getenv("EXPIRY_MINUTE", 30))
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Validate that SECRET_KEY is set
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY or JWT_SECRET_KEY environment variable is not set. "
        "Set one in your .env file: JWT_SECRET_KEY=your-secret-key"
    )

print(f"SECRET_KEY loaded: {SECRET_KEY}")
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    
    # 1. Set the Expiry
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRY_MINUTE)
    
    # 2. Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),  
        # Removed 'jti' since Redis blacklist is no longer used
    })
    
    # 3. Sign and Encode
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def _is_blacklisted(jti: str) -> bool:
    from database import SessionLocal
    from model.model import TokenBlacklist

    db = SessionLocal()
    try:
        return db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti
        ).first() is not None
    finally:
        db.close()


def require_auth(f):
    """
    Extracts token, validates it, and stores payload in Flask's `g` object.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract JWT (Checking both Cookie and Header)
        token = request.cookies.get("access_token") or request.headers.get("Authorization")
        
        if not token:
            return jsonify({"detail": "Not authenticated"}), 401
        
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            jti = payload.get("jti")
            if jti and _is_blacklisted(jti):
              return jsonify({"detail": "Token has been revoked"}), 401
            # Store the user payload in Flask's global context 'g'
            # This makes the user data available to the route function
            g.user = payload
            
        except ExpiredSignatureError:
            return jsonify({"detail": "Token has expired"}), 401
        except JWTError:
            return jsonify({"detail": "Could not validate credentials"}), 401
            
        return f(*args, **kwargs)
        
    return decorated_function


def require_role(allowed_roles: list):
    """
    Must be stacked AFTER @require_auth.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Retrieve user from the global context
            user = getattr(g, 'user', None)
            
            # Failsafe in case @require_auth was forgotten
            if not user:
                return jsonify({"detail": "Not authenticated"}), 401
                
            # Check role
            if user.get("role") not in allowed_roles:
                return jsonify({"detail": "Operation not permitted"}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator