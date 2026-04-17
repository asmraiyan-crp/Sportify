# ⚠️ DEPRECATED: RLS Policies (DELETE THIS FILE)

## DO NOT USE THIS FILE ANYMORE

The file `db/rls.sql` contains Row Level Security (RLS) policies that are **NO LONGER NEEDED**.

### Why?

- ✅ RLS is disabled in the database migration
- ✅ Manual authentication is used instead
- ✅ JWT tokens handle authorization
- ✅ All RLS policies have been dropped

### What to Do?

**Option 1: Delete the file**
```bash
rm db/rls.sql
```

**Option 2: Archive it (keep for reference)**
```bash
mv db/rls.sql db/rls.sql.deprecated
```

---

## What Was in rls.sql?

The file contained 69 lines of RLS policies:

1. **Enable RLS on all tables** (lines 2-18)
   ```sql
   ALTER TABLE sport ENABLE ROW LEVEL SECURITY;
   -- ... for all tables
   ```

2. **Public read access policies** (lines 21-28)
   ```sql
   CREATE POLICY public_read_sport ON sport FOR SELECT USING (true);
   -- ... for other tables
   ```

3. **Authenticated user policies** (lines 31-49)
   ```sql
   CREATE POLICY auth_insert_review ON review FOR INSERT
   WITH CHECK (auth.uid() = user_id);
   -- ... other policies
   ```

4. **Role-based policies** (lines 52-68)
   ```sql
   CREATE POLICY manager_update_player ON player FOR UPDATE
   USING ((SELECT role FROM profiles WHERE id = auth.uid()) = 'team_manager'
   AND team_id = (SELECT team_managed FROM profiles WHERE id = auth.uid()));
   ```

---

## Why Are RLS Policies Removed?

### Supabase RLS Uses: `auth.uid()` and `auth.users`

Your old RLS policies depended on:
```sql
-- This function is ONLY available when using Supabase Auth
auth.uid()  -- Current user ID from auth.users table

-- This table is ONLY available with Supabase Auth
auth.users  -- Supabase's authentication table
```

### You're Now Using: Manual JWT Authentication

```python
# Backend validates JWT token
valid, payload, error = verify_token(token)
user_id = payload.get('sub')  # Extract user ID from token

# Database doesn't need RLS because:
# - Authentication happens in Python code
# - Authorization is handled by Flask decorators
# - No dependency on Supabase auth tables
```

---

## Migration Path

| Aspect | Before (RLS) | After (Manual JWT) |
|--------|-------------|-------------------|
| Authentication | Supabase auth.users | PostgreSQL profiles + JWT |
| Authorization | RLS policies | Python decorators (@token_required) |
| User ID | UUID from auth.users | UUID in profiles table |
| Database | Supabase managed | PostgreSQL on Supabase |
| Control | Supabase provides | You control |

---

## What Replaced RLS?

### 1. SQLAlchemy ORM Models
```python
# Define data structure and relationships
class Profile(Base):
    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String)  # 'admin', 'team_manager', 'fan'
```

### 2. JWT Authentication
```python
# Create tokens on login
access_token = create_access_token(user_id)

# Validate tokens on protected endpoints
@token_required
def protected_endpoint():
    # request.user_id is available
    pass
```

### 3. Backend Authorization
```python
# Check user role in Python
@app.get('/admin/users')
@token_required
def admin_only():
    user = db.query(Profile).filter_by(id=request.user_id).first()
    if user.role != 'admin':
        return failure("FORBIDDEN", "Admin only", 403)
    # ... admin logic
```

---

## SQL Migration Removed RLS

Here's what the migration does:

```sql
-- 1. Disable RLS on all tables
ALTER TABLE sport DISABLE ROW LEVEL SECURITY;
ALTER TABLE league DISABLE ROW LEVEL SECURITY;
-- ... (for all tables)

-- 2. Drop all RLS policies
DROP POLICY IF EXISTS public_read_sport ON sport;
DROP POLICY IF EXISTS auth_insert_review ON review;
-- ... (for all policies)

-- 3. Create UUID-based tables instead
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255),  -- Bcrypt hashed
  -- ... rest of columns
);

-- 4. Update foreign keys to use UUID
ALTER TABLE review 
ADD CONSTRAINT review_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES profiles(id);
-- ... (for all referencing tables)
```

---

## Verify RLS is Disabled

Check in Supabase SQL console:

```sql
-- Check RLS status on profiles table
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'profiles';

-- Should show: rowsecurity = false

-- Check that policies were dropped
SELECT policyname
FROM pg_policies
WHERE tablename = 'profiles';

-- Should return: (no rows)
```

---

## File Cleanup

After migration, you can clean up old RLS files:

```bash
# Option 1: Delete
rm db/rls.sql

# Option 2: Archive
mv db/rls.sql db/archive/rls.sql.backup

# Keep the migration file
# db/migrations/01_disable_rls_and_setup_uuid.sql  ← KEEP THIS
```

---

## Summary

✅ **OLD SYSTEM (with RLS):**
- Row Level Security policies
- Supabase auth.users dependency
- Database enforced authorization
- Complex policy syntax

❌ **NO LONGER USED**
- rls.sql file
- auth.users table
- RLS policies
- Supabase auth functions

✅ **NEW SYSTEM (Manual JWT):**
- JWT tokens
- Backend authorization
- Python decorators
- Bcrypt password hashing
- Simple, flexible, controllable

---

## File Status

| File | Status | Action |
|------|--------|--------|
| `db/rls.sql` | ❌ DEPRECATED | DELETE |
| `db/schema.sql` | ✅ KEEP | Still needed |
| `db/seeds.sql` | ✅ KEEP | Still needed |
| `db/migrations/01_disable_rls_and_setup_uuid.sql` | ✅ NEW | RUN ONCE |

---

**Decision: DELETE or ARCHIVE `db/rls.sql`**

It is no longer used and can be safely removed from your codebase.

The migration `db/migrations/01_disable_rls_and_setup_uuid.sql` already removes all RLS.
