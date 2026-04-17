-- ════════════════════════════════════════════════════════════════════════════
-- MIGRATION 01: Disable RLS & Setup UUID for Manual Authentication
-- ════════════════════════════════════════════════════════════════════════════
-- This migration removes all RLS policies and prepares the database for
-- manual authentication using JWT tokens instead of Supabase auth.
-- ════════════════════════════════════════════════════════════════════════════

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 1: Disable RLS on all tables
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALTER TABLE sport DISABLE ROW LEVEL SECURITY;
ALTER TABLE league DISABLE ROW LEVEL SECURITY;
ALTER TABLE team DISABLE ROW LEVEL SECURITY;
ALTER TABLE team_league DISABLE ROW LEVEL SECURITY;
ALTER TABLE player DISABLE ROW LEVEL SECURITY;
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE game_match DISABLE ROW LEVEL SECURITY;
ALTER TABLE player_match_stat DISABLE ROW LEVEL SECURITY;
ALTER TABLE review DISABLE ROW LEVEL SECURITY;
ALTER TABLE comment DISABLE ROW LEVEL SECURITY;
ALTER TABLE player_rating DISABLE ROW LEVEL SECURITY;
ALTER TABLE highlight DISABLE ROW LEVEL SECURITY;
ALTER TABLE fan_event DISABLE ROW LEVEL SECURITY;
ALTER TABLE event_registration DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_follow_team DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_follow_player DISABLE ROW LEVEL SECURITY;
ALTER TABLE sync_log DISABLE ROW LEVEL SECURITY;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 2: Drop all RLS policies
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DROP POLICY IF EXISTS public_read_sport ON sport;
DROP POLICY IF EXISTS public_read_league ON league;
DROP POLICY IF EXISTS public_read_team ON team;
DROP POLICY IF EXISTS public_read_match ON game_match;
DROP POLICY IF EXISTS public_read_player ON player;
DROP POLICY IF EXISTS public_read_review ON review;
DROP POLICY IF EXISTS public_read_comment ON comment;
DROP POLICY IF EXISTS public_read_event ON fan_event;

DROP POLICY IF EXISTS auth_insert_review ON review;
DROP POLICY IF EXISTS auth_delete_review ON review;
DROP POLICY IF EXISTS auth_insert_comment ON comment;
DROP POLICY IF EXISTS auth_edit_comment ON comment;
DROP POLICY IF EXISTS auth_delete_comment ON comment;
DROP POLICY IF EXISTS auth_follow_team ON user_follow_team;
DROP POLICY IF EXISTS auth_follow_player ON user_follow_player;
DROP POLICY IF EXISTS auth_register_event ON event_registration;

DROP POLICY IF EXISTS manager_update_player ON player;
DROP POLICY IF EXISTS admin_all ON profiles;
DROP POLICY IF EXISTS own_profile_select ON profiles;
DROP POLICY IF EXISTS own_profile_update ON profiles;
DROP POLICY IF EXISTS admin_read_sync_log ON sync_log;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 3: Enable UUID extension
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 4: Drop old auth trigger and function (if exists)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS handle_new_user();

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 5: Backup old profiles data (if migrating from old schema)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- If you have existing data in profiles, this preserves it
CREATE TABLE IF NOT EXISTS profiles_backup AS SELECT * FROM profiles WHERE false;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 6: Drop and recreate profiles table with UUID
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- First, save data if exists
INSERT INTO profiles_backup SELECT * FROM profiles;

-- Drop foreign key constraints that reference profiles
ALTER TABLE review DROP CONSTRAINT IF EXISTS review_user_id_fkey;
ALTER TABLE comment DROP CONSTRAINT IF EXISTS comment_user_id_fkey;
ALTER TABLE player_rating DROP CONSTRAINT IF EXISTS player_rating_user_id_fkey;
ALTER TABLE highlight DROP CONSTRAINT IF EXISTS highlight_added_by_fkey;
ALTER TABLE fan_event DROP CONSTRAINT IF EXISTS fan_event_created_by_fkey;
ALTER TABLE event_registration DROP CONSTRAINT IF EXISTS event_registration_user_id_fkey;
ALTER TABLE user_follow_team DROP CONSTRAINT IF EXISTS user_follow_team_user_id_fkey;
ALTER TABLE user_follow_player DROP CONSTRAINT IF EXISTS user_follow_player_user_id_fkey;

-- Drop profiles table
DROP TABLE IF EXISTS profiles CASCADE;

-- Create new profiles table with UUID primary key
CREATE TABLE profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) NOT NULL UNIQUE,
  display_name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'fan'
    CHECK (role IN ('admin','team_manager','fan')),
  team_managed BIGINT REFERENCES team(team_id) ON DELETE SET NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 7: Restore foreign key constraints with UUID
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALTER TABLE review 
ADD CONSTRAINT review_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE comment 
ADD CONSTRAINT comment_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE player_rating 
ADD CONSTRAINT player_rating_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE highlight 
ADD CONSTRAINT highlight_added_by_fkey 
FOREIGN KEY (added_by) REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE fan_event 
ADD CONSTRAINT fan_event_created_by_fkey 
FOREIGN KEY (created_by) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE event_registration 
ADD CONSTRAINT event_registration_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE user_follow_team 
ADD CONSTRAINT user_follow_team_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE user_follow_player 
ADD CONSTRAINT user_follow_player_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 8: Create table for storing JWT tokens (optional, for blacklist)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATE TABLE IF NOT EXISTS jwt_blacklist (
  token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  token_jti VARCHAR(255) NOT NULL UNIQUE,
  blacklisted_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_user_id ON jwt_blacklist(user_id);
CREATE INDEX IF NOT EXISTS idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 9: Create indexes for better performance
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_review_user_id ON review(user_id);
CREATE INDEX IF NOT EXISTS idx_comment_user_id ON comment(user_id);
CREATE INDEX IF NOT EXISTS idx_player_rating_user_id ON player_rating(user_id);
CREATE INDEX IF NOT EXISTS idx_fan_event_created_by ON fan_event(created_by);
CREATE INDEX IF NOT EXISTS idx_event_registration_user_id ON event_registration(user_id);
CREATE INDEX IF NOT EXISTS idx_user_follow_team_user_id ON user_follow_team(user_id);
CREATE INDEX IF NOT EXISTS idx_user_follow_player_user_id ON user_follow_player(user_id);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STEP 10: Cleanup backup table (optional - delete after verifying)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- DROP TABLE profiles_backup; -- Uncomment after verification

-- ════════════════════════════════════════════════════════════════════════════
-- ✅ MIGRATION COMPLETE
-- ════════════════════════════════════════════════════════════════════════════
-- Your database is now ready for manual authentication with JWT tokens!
-- 
-- Next steps in your Python backend:
-- 1. Use UUID for user_id instead of BigInteger
-- 2. Implement JWT token generation in auth.py
-- 3. Add password hashing with bcrypt
-- 4. Use manual session/token validation
-- ════════════════════════════════════════════════════════════════════════════
