"""SportMonks Historical Match Seeder - Populates database with past matches."""

import os
import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timezone, timedelta

# Use find_dotenv() to ensure it finds the .env file from anywhere
load_dotenv(find_dotenv())

SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY")

# 1. Check for full DATABASE_URL first
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Fallback to building it from parts
if not DATABASE_URL or "None" in DATABASE_URL:
    DATABASE_USER = os.getenv("DATABASE_USER", "postgres.pyahykjyflsxnzlzudep")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "QcFDM5kKBO2pE2Qn")
    DATABASE_HOST = os.getenv("DATABASE_HOST", "aws-1-ap-northeast-1.pooler.supabase.com")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "6543")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")
    DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Strip out SQLAlchemy specific prefixes for psycopg2
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")

if not SPORTMONKS_API_KEY:
    raise ValueError("SPORTMONKS_API_KEY must be set in .env")

BASE_URL = "https://api.sportmonks.com/v3/football"
HEADERS = {"Authorization": SPORTMONKS_API_KEY}

# Premium leagues
LEAGUES_TO_SEED = [
    {"id": 8, "name": "Premier League", "country": "England"},
    {"id": 564, "name": "La Liga", "country": "Spain"},
    {"id": 570, "name": "Copa del Rey", "country": "Spain"},
    {"id": 82, "name": "Bundesliga", "country": "Germany"},
    {"id": 574, "name": "Supercopa de España", "country": "Spain"},
    {"id": 24, "name": "UEFA Super Cup", "country": "Europe"} 
]

STATUS_MAP = {
    "NS": "scheduled", 
    "FT": "finished", 
    "AET": "finished", 
    "PEN_BREAK": "finished", 
    "POSTP": "postponed", 
    "CANCL": "cancelled"
}


def get_db_connection():
    """Create a psycopg2 connection with SSL enabled for Supabase."""
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def seed_historical_matches(conn, start_date_str, end_date_str, target_leagues=None):
    """Fetches matches in 30-day chunks to bypass the SportMonks 31-day limit."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n=== Seeding Historical Matches ({start_date_str} to {end_date_str}) ===")
    
    leagues = target_leagues if target_leagues else LEAGUES_TO_SEED
    total_matches_inserted = 0

    # Convert strings to datetime objects for chunking math
    overall_start = datetime.strptime(start_date_str, "%Y-%m-%d")
    overall_end = datetime.strptime(end_date_str, "%Y-%m-%d")

    for league in leagues:
        league_ext_id = league["id"]
        league_name = league["name"]
        
        print(f"\n  Processing {league_name}...")

        # 1. Get internal League ID
        cur.execute("SELECT league_id FROM league WHERE external_api_id = %s", (str(league_ext_id),))
        league_row = cur.fetchone()
        if not league_row:
            print(f"    ✗ League not found in database. Run seed.py first. Skipping...")
            continue
        
        internal_league_id = league_row["league_id"]
        league_matches_inserted = 0

        # 2. Chop the massive date range into 30-day windows
        current_start = overall_start
        
        while current_start <= overall_end:
            current_end = current_start + timedelta(days=30)
            if current_end > overall_end:
                current_end = overall_end

            str_start = current_start.strftime("%Y-%m-%d")
            str_end = current_end.strftime("%Y-%m-%d")
            
            print(f"    Fetching window: {str_start} to {str_end}...")

            url = f"{BASE_URL}/fixtures/between/{str_start}/{str_end}"
            params = {
                "include": "participants;scores;state",
                "filters": f"fixtureLeagues:{league_ext_id}"
            }
            
            response = requests.get(url, headers=HEADERS, params=params)
            
            # Handle rate limits gracefully
            if response.status_code == 429:
                print("    ⚠ API Rate limit hit! Sleeping for 5 seconds...")
                time.sleep(5)
                continue  # Retry the exact same date window
            
            if response.status_code != 200:
                print(f"    ✗ Failed window (Code {response.status_code}). Skipping to next month...")
                current_start = current_end + timedelta(days=1)
                time.sleep(1)
                continue

            fixtures = response.json().get("data", [])
            
            for fixture in fixtures:
                ext_fixture_id = str(fixture["id"])
                match_datetime = fixture["starting_at"]
                
                # Parse Status
                state_code = fixture.get("state", {}).get("short_name", "NS")
                status = STATUS_MAP.get(state_code, "finished") 

                # Parse Participants (Home and Away Teams)
                home_team = next((p for p in fixture.get("participants", []) if p["meta"]["location"] == "home"), None)
                away_team = next((p for p in fixture.get("participants", []) if p["meta"]["location"] == "away"), None)

                if not home_team or not away_team:
                    continue

                # Parse Scores
                home_score, away_score = 0, 0
                for score in fixture.get("scores", []):
                    if score.get("description") == "CURRENT":
                        if score["score"]["participant"] == "home":
                            home_score = score["score"]["goals"]
                        elif score["score"]["participant"] == "away":
                            away_score = score["score"]["goals"]

                # 3. Ensure Teams Exist
                internal_team_ids = {}
                for team in [home_team, away_team]:
                    ext_team_id = str(team["id"])
                    team_name = team["name"]
                    logo = team.get("image_path", "")
                    
                    cur.execute("""
                        INSERT INTO team (sport_id, name, logo_url, external_api_id, created_at)
                        VALUES (1, %s, %s, %s, %s)
                        ON CONFLICT (external_api_id) DO UPDATE SET 
                            name = EXCLUDED.name,
                            logo_url = EXCLUDED.logo_url
                        RETURNING team_id;
                    """, (team_name, logo, ext_team_id, datetime.now(timezone.utc)))
                    
                    internal_team_ids[ext_team_id] = cur.fetchone()["team_id"]
                    
                    # Ensure junction table exists
                    cur.execute("""
                        INSERT INTO team_league (team_id, league_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;
                    """, (internal_team_ids[ext_team_id], internal_league_id))

                # 4. Upsert the Match
                cur.execute("""
                    INSERT INTO game_match (league_id, home_team_id, away_team_id, match_datetime, 
                                           status, home_score, away_score, external_api_id, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (external_api_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        home_score = EXCLUDED.home_score,
                        away_score = EXCLUDED.away_score,
                        match_datetime = EXCLUDED.match_datetime,
                        updated_at = NOW();
                """, (
                    internal_league_id,
                    internal_team_ids[str(home_team["id"])],
                    internal_team_ids[str(away_team["id"])],
                    match_datetime,
                    status,
                    home_score,
                    away_score,
                    ext_fixture_id,
                    datetime.now(timezone.utc)
                ))
                
                league_matches_inserted += 1
                total_matches_inserted += 1

            conn.commit()
            
            # Step forward by 1 month and pause to respect the API limits
            current_start = current_end + timedelta(days=1)
            time.sleep(0.5)

        print(f"    ✓ Synced {league_matches_inserted} total matches for {league_name}.")

    print(f"\n  ✓ Grand total historical matches seeded: {total_matches_inserted}")
    cur.close()


def main():
    """Run the historical seeder."""
    conn = None
    try:
        conn = get_db_connection()
        print("\n✓ Connected to database")
        
        # Define the date range for the 2023-2024 season
        START_DATE = "2023-08-01"
        END_DATE = "2024-06-01"
        
        seed_historical_matches(conn, START_DATE, END_DATE)
        
        print("\n✓ Historical seeding complete!")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
    
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()