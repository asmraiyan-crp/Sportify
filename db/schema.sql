-- sport
CREATE TABLE sport (
  sport_id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- league
CREATE TABLE league (
  league_id BIGSERIAL PRIMARY KEY,
  sport_id BIGINT NOT NULL REFERENCES sport(sport_id)
  ON DELETE RESTRICT ON UPDATE CASCADE,
  name TEXT NOT NULL,
  country TEXT,
  season TEXT NOT NULL,
  external_api_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(name, season)
);

-- team
CREATE TABLE team (
  team_id BIGSERIAL PRIMARY KEY,
  sport_id BIGINT NOT NULL REFERENCES sport(sport_id)
  ON DELETE RESTRICT ON UPDATE CASCADE,
  name TEXT NOT NULL,
  country TEXT,
  founded_year INT,
  home_ground TEXT,
  logo_url TEXT,
  external_api_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- team_league (junction)
CREATE TABLE team_league (
  team_id BIGINT NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
  league_id BIGINT NOT NULL REFERENCES league(league_id) ON DELETE CASCADE,
  PRIMARY KEY (team_id, league_id)
);

-- profiles (extends Supabase auth.users)
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  role TEXT NOT NULL DEFAULT 'fan'
  CHECK (role IN ('admin','team_manager','fan')),
  team_managed BIGINT REFERENCES team(team_id) ON DELETE SET NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile row when a new user signs up
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, display_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'display_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- player
CREATE TABLE player (
  player_id BIGSERIAL PRIMARY KEY,
  team_id BIGINT REFERENCES team(team_id) ON DELETE SET NULL,
  sport_id BIGINT NOT NULL REFERENCES sport(sport_id) ON DELETE RESTRICT,
  name TEXT NOT NULL,
  nationality TEXT,
  date_of_birth DATE,
  position_role TEXT,
  jersey_number SMALLINT,
  profile_image_url TEXT,
  injury_status TEXT NOT NULL DEFAULT 'fit'
  CHECK (injury_status IN ('fit','injured','doubtful')),
  injury_updated_at TIMESTAMPTZ,
  external_api_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- game_match (renamed from 'match' — reserved word in PostgreSQL)
CREATE TABLE game_match (
  match_id BIGSERIAL PRIMARY KEY,
  league_id BIGINT NOT NULL REFERENCES league(league_id),
  home_team_id BIGINT NOT NULL REFERENCES team(team_id),
  away_team_id BIGINT NOT NULL REFERENCES team(team_id),
  match_datetime TIMESTAMPTZ NOT NULL,
  venue TEXT,
  status TEXT NOT NULL DEFAULT 'scheduled'
  CHECK (status IN ('scheduled','live','finished','postponed','cancelled')),
  home_score SMALLINT DEFAULT 0,
  away_score SMALLINT DEFAULT 0,
  elapsed_time SMALLINT,
  extra_data JSONB,
  external_api_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CHECK (home_team_id <> away_team_id)
);

-- Auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER game_match_updated_at
BEFORE UPDATE ON game_match
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- player_match_stat (junction)
CREATE TABLE player_match_stat (
  stat_id BIGSERIAL PRIMARY KEY,
  player_id BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  match_id BIGINT NOT NULL REFERENCES game_match(match_id) ON DELETE CASCADE,
  minutes_played SMALLINT DEFAULT 0,
  goals SMALLINT DEFAULT 0,
  assists SMALLINT DEFAULT 0,
  yellow_cards SMALLINT DEFAULT 0,
  red_cards SMALLINT DEFAULT 0,
  runs_scored SMALLINT DEFAULT 0,
  wickets SMALLINT DEFAULT 0,
  extra_stats JSONB,
  UNIQUE (player_id, match_id)
);

-- review
CREATE TABLE review (
  review_id BIGSERIAL PRIMARY KEY,
  match_id BIGINT NOT NULL REFERENCES game_match(match_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  body TEXT,
  is_hidden BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, match_id)
);

-- comment
CREATE TABLE comment (
  comment_id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('match','player')),
  entity_id BIGINT NOT NULL,
  parent_id BIGINT REFERENCES comment(comment_id) ON DELETE CASCADE,
  body TEXT NOT NULL,
  is_hidden BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  edited_at TIMESTAMPTZ
);

-- player_rating
CREATE TABLE player_rating (
  rating_id BIGSERIAL PRIMARY KEY,
  player_id BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  match_id BIGINT NOT NULL REFERENCES game_match(match_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (player_id, match_id, user_id)
);

-- highlight
CREATE TABLE highlight (
  highlight_id BIGSERIAL PRIMARY KEY,
  match_id BIGINT NOT NULL REFERENCES game_match(match_id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  video_url TEXT NOT NULL,
  added_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- fan_event
CREATE TABLE fan_event (
  event_id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  event_date TIMESTAMPTZ NOT NULL,
  location TEXT,
  capacity SMALLINT NOT NULL DEFAULT 100,
  created_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- event_registration (junction)
CREATE TABLE event_registration (
  registration_id BIGSERIAL PRIMARY KEY,
  event_id BIGINT NOT NULL REFERENCES fan_event(event_id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  registered_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (event_id, user_id)
);

-- user_follow_team (junction)
CREATE TABLE user_follow_team (
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  team_id BIGINT NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
  followed_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, team_id)
);

-- user_follow_player (junction)
CREATE TABLE user_follow_player (
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  player_id BIGINT NOT NULL REFERENCES player(player_id) ON DELETE CASCADE,
  followed_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, player_id)
);

-- sync_log
CREATE TABLE sync_log (
  log_id BIGSERIAL PRIMARY KEY,
  sync_type TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  records_fetched INT DEFAULT 0,
  records_upserted INT DEFAULT 0,
  status TEXT DEFAULT 'running'
  CHECK (status IN ('running','success','failed')),
  error_message TEXT
);

-- Indexes
CREATE INDEX idx_match_status ON game_match(status);
CREATE INDEX idx_match_datetime ON game_match(match_datetime);
CREATE INDEX idx_player_team ON player(team_id);
CREATE INDEX idx_comment_entity ON comment(entity_type, entity_id);
CREATE INDEX idx_review_match ON review(match_id);
CREATE INDEX idx_highlight_match ON highlight(match_id);
