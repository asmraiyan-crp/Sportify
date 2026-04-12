-- ■■ Enable RLS on all user-facing tables ■■■■■■■■■■■■■■■■■■■■■■■■
ALTER TABLE sport ENABLE ROW LEVEL SECURITY;
ALTER TABLE league ENABLE ROW LEVEL SECURITY;
ALTER TABLE team ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_league ENABLE ROW LEVEL SECURITY;
ALTER TABLE player ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_match ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_match_stat ENABLE ROW LEVEL SECURITY;
ALTER TABLE review ENABLE ROW LEVEL SECURITY;
ALTER TABLE comment ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_rating ENABLE ROW LEVEL SECURITY;
ALTER TABLE highlight ENABLE ROW LEVEL SECURITY;
ALTER TABLE fan_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_registration ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_follow_team ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_follow_player ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_log ENABLE ROW LEVEL SECURITY;

-- ■■ Public read access (sport, league, team, game_match, player) ■
CREATE POLICY public_read_sport ON sport FOR SELECT USING (true);
CREATE POLICY public_read_league ON league FOR SELECT USING (true);
CREATE POLICY public_read_team ON team FOR SELECT USING (true);
CREATE POLICY public_read_match ON game_match FOR SELECT USING (true);
CREATE POLICY public_read_player ON player FOR SELECT USING (true);
CREATE POLICY public_read_review ON review FOR SELECT USING (NOT is_hidden);
CREATE POLICY public_read_comment ON comment FOR SELECT USING (NOT is_hidden);
CREATE POLICY public_read_event ON fan_event FOR SELECT USING (true);

-- ■■ Authenticated users: insert/update/delete own rows ■■■■■■■■■■
CREATE POLICY auth_insert_review ON review FOR INSERT
WITH CHECK (auth.uid() = user_id);
CREATE POLICY auth_delete_review ON review FOR DELETE
USING (auth.uid() = user_id);
CREATE POLICY auth_insert_comment ON comment FOR INSERT
WITH CHECK (auth.uid() = user_id);
CREATE POLICY auth_edit_comment ON comment FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);
CREATE POLICY auth_delete_comment ON comment FOR DELETE
USING (auth.uid() = user_id OR
(SELECT role FROM profiles WHERE id = auth.uid()) = 'admin');

CREATE POLICY auth_follow_team ON user_follow_team FOR ALL
USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY auth_follow_player ON user_follow_player FOR ALL
USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY auth_register_event ON event_registration FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- ■■ Team Manager: update injury status for own team only ■■■■■■■■■
CREATE POLICY manager_update_player ON player FOR UPDATE
USING ((SELECT role FROM profiles WHERE id = auth.uid()) = 'team_manager'
AND team_id = (SELECT team_managed FROM profiles WHERE id = auth.uid()));

-- ■■ Admin: full access on all tables ■■■■■■■■■■■■■■■■■■■■■■■■■■■■
CREATE POLICY admin_all ON profiles FOR ALL
USING ((SELECT role FROM profiles WHERE id = auth.uid()) = 'admin');

-- ■■ Own profile: users can read/update their own profile ■■■■■■■■■
CREATE POLICY own_profile_select ON profiles FOR SELECT
USING (auth.uid() = id);
CREATE POLICY own_profile_update ON profiles FOR UPDATE
USING (auth.uid() = id);

-- ■■ sync_log: admin read only ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
CREATE POLICY admin_read_sync_log ON sync_log FOR SELECT
USING ((SELECT role FROM profiles WHERE id = auth.uid()) = 'admin');
