# Supabase Removal - PostgreSQL Only Setup

## What Was Changed

### ✅ Removed Supabase Features

1. **Removed `auth.users` dependency**
   - Profile model no longer references Supabase's auth.users table
   - Profile table is now completely standalone

2. **Removed UUID foreign keys**
   - Changed Profile.id from PG_UUID to BigInteger
   - Renamed id column to user_id for clarity
   - All references to auth users now use BigInteger

3. **Removed Supabase authentication**
   - Deleted `supabase_signup()` function from model.py
   - Removed Supabase environment variables from app.py
   - Removed all Supabase HTTP request code

4. **Removed RLS & Supabase features**
   - Profile no longer extends Supabase auth users
   - No more auth.users table dependency
   - Pure PostgreSQL-only backend

### 📝 Files Modified

#### 1. **model/model.py**
```diff
- UUID foreign key to auth.users
+ BigInteger user_id with local generation
- PG_UUID imports
+ Standard BigInteger type
- supabase_signup() function
+ Removed entirely
```

**Profile Model Changes:**
```python
# Before:
class Profile(Base):
    id = Column(PG_UUID(as_uuid=True), primary_key=True)  # References auth.users

# After:
class Profile(Base):
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
```

#### 2. **app.py**
```diff
- SUPABASE_URL config
- SUPABASE_ANON_KEY config
+ Clean Flask configuration
```

#### 3. **api/v1/auth.py**
```diff
- Supabase signup integration
- Supabase HTTP requests
+ Local user registration
+ Local authentication
+ Database-backed user storage
```

**New Auth Endpoints:**
- `POST /api/v1/auth/signup` - Register new user locally
- `POST /api/v1/auth/login` - Authenticate user (local)

### 🔄 All Models Updated

The following models were updated to use BigInteger instead of UUID:

1. **Review** - user_id: UUID → BigInteger
2. **Comment** - user_id: UUID → BigInteger
3. **PlayerRating** - user_id: UUID → BigInteger
4. **Highlight** - added_by: UUID → BigInteger
5. **FanEvent** - created_by: UUID → BigInteger
6. **EventRegistration** - user_id: UUID → BigInteger
7. **UserFollowTeam** - user_id: UUID → BigInteger
8. **UserFollowPlayer** - user_id: UUID → BigInteger

All foreign keys now reference `profiles.user_id` instead of `profiles.id`.

## How to Use

### 1. Set Up PostgreSQL on Supabase

```bash
# Create database in Supabase Console
# Get connection string from Supabase settings
```

### 2. Configure Database URL

```bash
export DATABASE_URL="postgresql://user:password@db.supabase.co:5432/postgres"
```

### 3. Initialize Database

```bash
python3 app.py
```

The app will automatically create all tables on startup.

### 4. User Registration

```bash
curl -X POST http://localhost:5000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "display_name": "John Doe"
  }'
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "user_id": 1,
    "email": "user@example.com",
    "display_name": "John Doe",
    "role": "fan"
  }
}
```

### 5. User Login

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

## Database Schema Changes

### Old Schema (with Supabase)
```sql
-- Depended on Supabase's auth.users table
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  ...
)
```

### New Schema (PostgreSQL only)
```sql
-- Completely independent
CREATE TABLE profiles (
  user_id BIGSERIAL PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  display_name VARCHAR,
  role VARCHAR DEFAULT 'fan',
  team_managed BIGINT REFERENCES team(team_id),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
)
```

## Key Improvements

✅ **Simplified Architecture**
- No Supabase auth dependency
- Easier to customize user authentication
- Full control over user management

✅ **Cost Reduction**
- No Supabase auth usage charges
- Only paying for PostgreSQL storage

✅ **Better Scalability**
- Easy to implement custom auth (JWT, sessions, etc.)
- Can implement password hashing, rate limiting, etc.

✅ **Cleaner Codebase**
- No external service dependencies
- Fewer environment variables to manage
- Simpler deployment

## Supabase Usage

**Supabase is now used for:**
- PostgreSQL database hosting only
- Connection URL and credentials
- Database backups and recovery

**Supabase features NOT used:**
- ❌ Authentication (auth.users)
- ❌ Row Level Security (RLS)
- ❌ Supabase Realtime
- ❌ Supabase Edge Functions

## Migration from Old Setup

If you had existing Supabase users in `auth.users`:

1. Export data from Supabase auth.users
2. Import into the new profiles table
3. Map UUID auth.users.id to profiles.user_id
4. Test all relationships work correctly

## Next Steps

1. ✅ Set up PostgreSQL on Supabase
2. ✅ Configure DATABASE_URL
3. ✅ Start Flask backend
4. ✅ Test signup/login endpoints
5. 🔜 Implement JWT tokens for session management (optional)
6. 🔜 Add password hashing (implement with bcrypt)
7. 🔜 Add email verification (optional)

## File Structure

```
backend/
├── model/model.py              ← 17 ORM models (PostgreSQL only)
├── api/v1/auth.py              ← Local authentication
├── app.py                       ← Flask app (no Supabase)
├── database.py                  ← PostgreSQL connection
└── DATABASE_SETUP.md            ← Setup guide
```

## Testing

Run the test endpoints to verify setup:

```bash
# Health check
curl http://localhost:5000/api/v1/test/health

# Model info
curl http://localhost:5000/api/v1/test/models-info

# DB connection
curl http://localhost:5000/api/v1/test/db-test
```

## Summary

Your Sportify backend is now:
- ✅ Using PostgreSQL only (hosted on Supabase)
- ✅ Free from Supabase's authentication layer
- ✅ Ready for local user management
- ✅ Simpler and more maintainable
- ✅ Fully compatible with 17 ORM models

All Supabase dependencies have been removed. Use Supabase only as your PostgreSQL provider.
