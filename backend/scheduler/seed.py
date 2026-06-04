"""SportMonks Seeder - Populates database with leagues, teams, and players."""

import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY")

DATABASE_USER = os.getenv("DATABASE_USER", "postgres.pyahykjyflsxnzlzudep")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "QcFDM5kKBO2pE2Qn")
DATABASE_HOST = os.getenv("DATABASE_HOST", "aws-1-ap-northeast-1.pooler.supabase.com")
DATABASE_PORT = os.getenv("DATABASE_PORT", "6543")
DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")

# Construct psycopg2 connection string
PSYCOPG2_DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

if not SPORTMONKS_API_KEY:
    raise ValueError("SPORTMONKS_API_KEY must be set in .env")

BASE_URL = "https://api.sportmonks.com/v3/football"
HEADERS = {"Authorization": SPORTMONKS_API_KEY}

# SportMonks free tier leagues ONLY (Option A)
# The season IDs will be fetched dynamically, so the hardcoded ones here are just fallbacks
LEAGUES_TO_SEED = [
    {"id": 501, "name": "Scottish Premiership", "season_id": 23672, "country": "Scotland"}, 
    {"id": 271, "name": "Danish Superliga", "season_id": 23611, "country": "Denmark"},
]

def get_db_connection():
    """Create a psycopg2 connection with SSL enabled for Supabase."""
    return psycopg2.connect(PSYCOPG2_DATABASE_URL, sslmode="require")


def seed_leagues(conn):
    """Seed the league table from SportMonks API."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n=== Seeding Leagues ===")
    
    for league in LEAGUES_TO_SEED:
        external_id = str(league["id"])
        name = league["name"]
        country = league["country"]
        season = "2024-25"
        
        print(f"  Seeding: {name} ({country})...")
        
        cur.execute("""
            INSERT INTO league (sport_id, name, country, season, external_api_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name, season) DO UPDATE SET
                external_api_id = EXCLUDED.external_api_id,
                country = EXCLUDED.country
            RETURNING league_id;
        """, (1, name, country, season, external_id, datetime.now(timezone.utc)))
        
        result = cur.fetchone()
        league["league_id"] = result["league_id"]
        conn.commit()
    
    print(f"  ✓ Seeded {len(LEAGUES_TO_SEED)} leagues")
    cur.close()


def seed_teams(conn):
    """Seed the team table for each league using SportMonks API."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n=== Seeding Teams ===")
    
    total_teams = 0
    
    for league in LEAGUES_TO_SEED:
        league_id = league["id"] 
        db_league_id = league["league_id"] 
        league_name = league["name"]
        
        print(f"  Fetching current season for {league_name}...")
        
        # 1. Dynamically find the active season ID
        league_url = f"{BASE_URL}/leagues/{league_id}"
        season_resp = requests.get(league_url, headers=HEADERS, params={"include": "currentSeason"})
        
        if season_resp.status_code != 200:
            print(f"    ✗ Failed to fetch league info for {league_name}.")
            continue
            
        season_data = season_resp.json()
        current_season = season_data.get("data", {}).get("currentseason", {})
        season_id = current_season.get("id")
        
        if not season_id:
            print(f"    ✗ No active season found for {league_name}. Skipping...")
            continue
            
        print(f"    Found active season ID: {season_id}. Fetching teams...")
        
        # 2. Fetch teams using the dynamic season_id
        teams_url = f"{BASE_URL}/teams/seasons/{season_id}"
        response = requests.get(teams_url, headers=HEADERS, params={"per_page": 100})
        
        if response.status_code != 200:
            print(f"    ✗ Failed to fetch teams: {response.status_code}")
            continue
        
        data = response.json()
        teams = data.get("data", [])
        
        print(f"    Found {len(teams)} teams, inserting...")
        
        for team in teams:
            team_ext_id = str(team["id"])
            team_name = team.get("name", "")
            country = team.get("country", "")
            founded = team.get("founded", None)
            logo = team.get("image_path", "")
            
            # Insert into team table
            cur.execute("""
                INSERT INTO team (sport_id, name, country, founded_year, logo_url, external_api_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_api_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    country = EXCLUDED.country,
                    founded_year = EXCLUDED.founded_year,
                    logo_url = EXCLUDED.logo_url
                RETURNING team_id;
            """, (1, team_name, country, founded, logo, team_ext_id, datetime.now(timezone.utc)))
            
            result = cur.fetchone()
            inserted_team_id = result["team_id"]
            
            # Insert into team_league junction table
            cur.execute("""
                INSERT INTO team_league (team_id, league_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
            """, (inserted_team_id, db_league_id))
            
            total_teams += 1
        
        conn.commit()
        print(f"    ✓ Seeded {len(teams)} teams for {league_name}")
    
    print(f"  ✓ Total teams seeded: {total_teams}")
    cur.close()


def seed_players(conn):
    """Seed the player table for each team using SportMonks API."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n=== Seeding Players ===")
    
    # Get all teams from database
    cur.execute("""
        SELECT team_id, external_api_id FROM team WHERE sport_id = 1;
    """)
    
    teams = cur.fetchall()
    print(f"  Found {len(teams)} teams in database")
    
    total_players = 0
    
    for team in teams:
        team_id = team["team_id"]
        team_ext_id = team["external_api_id"]
        
        # --- NEW CODE: Use Squads endpoint with proper includes ---
        url = f"{BASE_URL}/squads/teams/{team_ext_id}"
        params = {
            "include": "player.position;player.nationality",
            "per_page": 100
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"    ✗ Failed to fetch players for team {team_ext_id}: {response.status_code}")
            print(f"      URL: {url}")
            print(f"      Response: {response.text[:200]}")
            continue
        
        data = response.json()
        squad_entries = data.get("data", [])
        
        players_seeded = 0
        
        for entry in squad_entries:
            # Extract the actual player data from the squad entry
            player = entry.get("player")
            if not player:
                continue
                
            player_id = str(player["id"])
            
            # --- THE FIX: Use 'or' to safely catch None values ---
            display_name = player.get("display_name") or player.get("name") or "Unknown Player"
            
            nationality_obj = player.get("nationality") or {}
            nationality = nationality_obj.get("name") or "Unknown"
            
            position_obj = player.get("position") or {}
            position_role = position_obj.get("developer_name") or "Unknown"
            
            image_path = player.get("image_path") or ""
            # -----------------------------------------------------
            
            # Insert into player table
            cur.execute("""
                INSERT INTO player (team_id, sport_id, name, nationality, position_role, 
                                   profile_image_url, external_api_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_api_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    nationality = EXCLUDED.nationality,
                    position_role = EXCLUDED.position_role,
                    profile_image_url = EXCLUDED.profile_image_url
                RETURNING player_id;
            """, (team_id, 1, display_name, nationality, position_role, 
                  image_path, player_id, datetime.now(timezone.utc)))
            
            players_seeded += 1
            total_players += 1
        
        if players_seeded > 0:
            print(f"    ✓ Seeded {players_seeded} players for team {team_ext_id}")
        
        conn.commit()
    
    print(f"  ✓ Total players seeded: {total_players}")
    cur.close()


def main():
    """Run the seeder."""
    conn = None
    try:
        conn = get_db_connection()
        print("\n✓ Connected to database")
        
        seed_leagues(conn)
        seed_teams(conn)
        seed_players(conn)
        
        print("\n✓ Seeding complete!")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
    
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()