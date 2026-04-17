# ════════════════════════════════════════════════════════════════════════════
# SUPABASE SETUP GUIDE: UUID WITH MANUAL JWT AUTHENTICATION
# ════════════════════════════════════════════════════════════════════════════

## Overview

This guide explains how to set up your Supabase PostgreSQL database for manual 
authentication using UUID and JWT tokens instead of Supabase's built-in auth.

**Key Benefits:**
- ✅ UUID for distributed system compatibility
- ✅ Manual control over authentication
- ✅ JWT tokens for stateless API
- ✅ Password hashing with bcrypt
- ✅ Supabase as database only (no auth dependency)
- ✅ Full flexibility for custom auth logic

---

## STEP 1: Run Migration in Supabase Console

1. Go to your Supabase dashboard
2. Click on "SQL" in the left sidebar
3. Create a new query
4. **Copy and paste the SQL from:** `db/migrations/01_disable_rls_and_setup_uuid.sql`
5. Click "Run"

**What this does:**
- Disables Row Level Security (RLS) on all tables
- Drops all RLS policies
- Enables UUID extension
- Creates new profiles table with UUID primary key
- Updates all foreign keys to reference UUID
- Drops old auth triggers
- Creates indexes for performance

---

## STEP 2: Verify Database Structure

After running the migration, verify the changes:

```sql
-- Check profiles table structure
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'profiles' 
ORDER BY ordinal_position;

-- Should show:
-- id                 | uuid
-- email              | character varying
-- password_hash      | character varying
-- display_name       | character varying
-- role               | character varying
-- team_managed       | bigint
-- is_active          | boolean
-- created_at         | timestamp with time zone
-- updated_at         | timestamp with time zone
```

---

## STEP 3: Update Python Backend

### 3a. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New packages added:**
- PyJWT==2.8.1 - For JWT token creation/validation
- bcrypt==4.1.1 - For password hashing

### 3b. Environment Configuration

Create `.env` file in `backend/` directory:

```env
# Database Connection
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
```

**Get your DATABASE_URL from Supabase:**
1. Go to Supabase Dashboard
2. Click "Settings" → "Database"
3. Copy the connection string under "URI"
4. Replace `[PASSWORD]` with your database password

### 3c. Verify Models Updated

All models now use UUID for user references:

```python
# Profile model uses UUID
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
password_hash = Column(String, nullable=True)

# All user-referencing models use UUID
user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id', ...))
```

---

## STEP 4: Test the Backend

### 4a. Start Backend Server

```bash
cd backend
python3 app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
```

### 4b. Test Health Endpoint

```bash
curl http://localhost:5000/api/v1/test/health
```

Response:
```json
{
  "ok": true,
  "data": {
    "status": "Backend is running",
    "database": "Connected"
  },
  "error": null
}
```

### 4c. Test User Registration

```bash
curl -X POST http://localhost:5000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "display_name": "John Doe"
  }'
```

Response (with JWT tokens):
```json
{
  "ok": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "John Doe",
    "role": "fan",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 1800
  },
  "error": null
}
```

### 4d. Test User Login

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "ok": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "John Doe",
    "role": "fan",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 1800
  },
  "error": null
}
```

### 4e. Test Authenticated Request

```bash
curl -X GET http://localhost:5000/api/v1/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

Response:
```json
{
  "ok": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "John Doe",
    "role": "fan",
    "is_active": true,
    "created_at": "2024-04-13T11:13:52+00:00"
  },
  "error": null
}
```

### 4f. Test Token Refresh

```bash
curl -X POST http://localhost:5000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

Response:
```json
{
  "ok": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 1800
  },
  "error": null
}
```

---

## AVAILABLE ENDPOINTS

### Authentication Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/auth/signup` | Register new user |
| POST | `/api/v1/auth/login` | Login user |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout user |
| GET | `/api/v1/auth/me` | Get current user (auth required) |
| PUT | `/api/v1/auth/me` | Update current user (auth required) |

### Test/Diagnostic Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/test/health` | Health check |
| GET | `/api/v1/test/status` | Detailed status |
| GET | `/api/v1/test/models-info` | Model information |
| GET | `/api/v1/test/db-test` | Database connectivity |
| POST | `/api/v1/test/db-init` | Initialize database |

---

## HOW IT WORKS: JWT AUTHENTICATION

### 1. User Registration (Signup)

```
1. User submits email + password
   ↓
2. Backend hashes password with bcrypt
   ↓
3. Creates Profile in database with:
   - id: UUID (auto-generated)
   - email: unique identifier
   - password_hash: bcrypt hash
   - role: 'fan' (default)
   ↓
4. Generates JWT tokens:
   - Access Token (expires in 30 min)
   - Refresh Token (expires in 7 days)
   ↓
5. Returns tokens to client
```

### 2. User Login

```
1. User submits email + password
   ↓
2. Backend queries profiles table for email
   ↓
3. Verifies password against stored hash
   ↓
4. Generates new JWT tokens
   ↓
5. Returns tokens to client
```

### 3. Authenticated Requests

```
1. Client includes: Authorization: Bearer <token>
   ↓
2. Backend validates JWT signature and expiration
   ↓
3. If valid, extracts user_id from token
   ↓
4. Processes request with user context
   ↓
5. Returns response
```

### 4. Token Refresh

```
1. Client sends refresh_token
   ↓
2. Backend validates refresh token
   ↓
3. Generates new access_token
   ↓
4. Client uses new access_token for requests
```

---

## JWT TOKEN STRUCTURE

### Access Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "type": "access",
  "exp": 1713100432,  // expiration timestamp
  "iat": 1713098632   // issued at timestamp
}
```

### Refresh Token Payload

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "type": "refresh",
  "exp": 1713703232,  // 7 days later
  "iat": 1713098632
}
```

---

## SECURITY BEST PRACTICES

✅ **Implemented:**
- Bcrypt password hashing
- JWT token expiration
- Separate access/refresh tokens
- UUID for user identification
- Email uniqueness constraint

🔜 **Recommended (Future):**
- HTTPS/TLS in production
- Token blacklist for logout
- Rate limiting on auth endpoints
- Email verification on signup
- Password reset functionality
- Two-factor authentication
- CORS policy configuration

---

## TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'jwt'"

**Solution:**
```bash
pip install PyJWT==2.8.1
pip install bcrypt==4.1.1
```

### Issue: "Invalid user_id in token"

**Cause:** Token contains invalid UUID format
**Solution:** Ensure frontend sends valid JWT tokens from `/login` response

### Issue: "Token has expired"

**Cause:** Access token (30 min expiration) has expired
**Solution:** Use refresh token to get new access token

### Issue: "Email already registered"

**Cause:** Trying to signup with existing email
**Solution:** Either login with existing account or use different email

### Issue: "Database connection failed"

**Solution:**
1. Verify DATABASE_URL environment variable
2. Check Supabase database is active
3. Verify credentials are correct
4. Test connection: `psql <DATABASE_URL>`

---

## MIGRATION FROM OLD SCHEMA

If you had existing users in Supabase auth.users:

```sql
-- Export from Supabase
SELECT id, email, raw_user_meta_data->>'display_name' as display_name 
FROM auth.users;

-- Import into new profiles table
INSERT INTO profiles (id, email, display_name, role, is_active)
SELECT id, email, display_name, 'fan', true
FROM exported_users;
```

---

## FILE STRUCTURE

```
backend/
├── model/model.py              ← UUID Profile model
├── api/v1/auth.py              ← JWT authentication
├── database.py                 ← PostgreSQL connection
├── app.py                       ← Flask application
├── requirements.txt            ← Dependencies (PyJWT, bcrypt)
└── .env                        ← Configuration (add this)

db/
├── schema.sql                  ← Original schema
├── rls.sql                     ← RLS policies (to delete)
└── migrations/
    └── 01_disable_rls_and_setup_uuid.sql  ← Run this
```

---

## SUMMARY

✅ **What Changed:**
- Profile.id: BigInteger → UUID (auto-generated)
- Profile.password_hash: Added (bcrypt)
- All user_id columns: BigInteger → UUID
- Authentication: Supabase auth → Manual JWT
- RLS Policies: All disabled

✅ **Backend Now Provides:**
- User registration with password hashing
- User login with JWT token generation
- Authenticated endpoints with token validation
- Token refresh mechanism
- Profile management endpoints

✅ **Your Database:**
- Uses Supabase as PostgreSQL provider only
- No Supabase auth dependency
- Manual authentication with JWT
- Full control over user management

---

## NEXT STEPS

1. ✅ Run migration SQL in Supabase
2. ✅ Update .env with DATABASE_URL
3. ✅ Install dependencies: `pip install -r requirements.txt`
4. ✅ Start backend: `python3 app.py`
5. ✅ Test endpoints as shown above
6. 🔜 Build frontend to consume auth endpoints
7. 🔜 Add additional API endpoints for sports features

---

*Guide created for Sportify Backend*
*Built with Flask, SQLAlchemy, PostgreSQL, JWT, and Bcrypt*
