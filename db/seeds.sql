-- Seed Sports
INSERT INTO sport (name, description) VALUES
  ('Football', 'Association football / soccer'),
  ('Cricket', 'Bat-and-ball game played between two teams of eleven players'),
  ('Wrestling', 'Combat sport involving grappling-type techniques');

-- Seed Leagues
INSERT INTO league (sport_id, name, country, season) VALUES
  (1, 'Premier League', 'England', '2023/24'),
  (1, 'La Liga', 'Spain', '2023/24'),
  (2, 'IPL', 'India', '2024'),
  (2, 'BBL', 'Australia', '2023/24'),
  (3, 'WWE', 'USA', '2024');

-- Seed Teams
INSERT INTO team (sport_id, name, country, founded_year, home_ground) VALUES
  (1, 'Arsenal FC', 'England', 1886, 'Emirates Stadium'),
  (1, 'Manchester City', 'England', 1880, 'Etihad Stadium'),
  (1, 'Real Madrid', 'Spain', 1902, 'Santiago Bernabéu'),
  (1, 'FC Barcelona', 'Spain', 1899, 'Camp Nou'),
  (2, 'Mumbai Indians', 'India', 2008, 'Wankhede Stadium'),
  (2, 'Chennai Super Kings', 'India', 2008, 'M. A. Chidambaram Stadium'),
  (3, 'Raw Roster', 'USA', 1993, 'Various'),
  (3, 'SmackDown Roster', 'USA', 1999, 'Various');

-- team_league mapping
INSERT INTO team_league (team_id, league_id) VALUES
  (1, 1),
  (2, 1),
  (3, 2),
  (4, 2);

-- Note: In an actual setup using Auth we would first insert users in auth.users
-- and triggers would create profiles. For raw DB seeding without auth endpoints,
-- this section may vary, so ensure to test auth integration via the application.
