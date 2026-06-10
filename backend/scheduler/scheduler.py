"""APScheduler background jobs for syncing SportMonks data."""

import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from .mapper import map_fixture, map_player_stat
from .resolver import IDResolver

load_dotenv()

SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY")

# Build psycopg2-compatible connection string from environment
DATABASE_USER = os.getenv("DATABASE_USER", "postgres.pyahykjyflsxnzlzudep")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "QcFDM5kKBO2pE2Qn")
DATABASE_HOST = os.getenv("DATABASE_HOST", "aws-1-ap-northeast-1.pooler.supabase.com")
DATABASE_PORT = os.getenv("DATABASE_PORT", "6543")
DATABASE_NAME = os.getenv("DATABASE_NAME", "postgres")

PSYCOPG2_DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

BASE_URL = "https://api.sportmonks.com/v3/football"
HEADERS = {"Authorization": SPORTMONKS_API_KEY}

_id_resolver = None


def get_resolver():
    """Lazy-load and cache the ID resolver."""
    global _id_resolver
    if _id_resolver is None:
        _id_resolver = IDResolver(PSYCOPG2_DATABASE_URL)
    return _id_resolver


def get_db_connection():
    """Create a psycopg2 connection with SSL enabled for Supabase."""
    return psycopg2.connect(PSYCOPG2_DATABASE_URL, sslmode="require")


def log_sync(conn, status, sync_type='live_scores', started_at=None, records_fetched=0, records_upserted=0, error_message=None):
    """
    Write to sync_log table.
    
    Args:
        conn: Database connection
        status: 'running', 'success', or 'failed'
        sync_type: Type of sync ('live_scores', 'fixtures', 'player_stats')
        started_at: Datetime object of when the job actually started
        records_fetched: Number of records fetched from API
        records_upserted: Number of records upserted to DB
        error_message: Error message if failed
    """
    cur = conn.cursor()
    now = datetime.now(timezone.utc)
    
    # If started_at wasn't provided, fallback to now to prevent NotNullViolation
    if started_at is None:
        started_at = now
        
    # finished_at is None if running, otherwise it's now
    finished_at = None if status == 'running' else now
    
    cur.execute("""
        INSERT INTO sync_log (sync_type, started_at, finished_at, records_fetched, records_upserted, status, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING log_id;
    """, (sync_type, started_at, finished_at, records_fetched, records_upserted, status, error_message))
    
    log_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    return log_id


def sync_live_scores():
    """JOB 1: Sync live scores every 60 seconds."""
    conn = None
    started_at = datetime.now(timezone.utc) # Track exact start time
    
    try:
        conn = get_db_connection()
        resolver = get_resolver()
        
        # Log start
        log_sync(conn, "running", 'live_scores', started_at=started_at)
        
        print("[SYNC] Fetching live scores...")
        
        # Fetch live fixtures
        
        # 🚀 FIXED: Use the correct V3 endpoint for live matches
        url = f"{BASE_URL}/livescores/inplay"
        params = {"include": "participants;scores;periods;state"}
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            msg = f"API returned {response.status_code}"
            # Log failure with the exact start time
            log_sync(conn, "failed", 'live_scores', started_at=started_at, error_message=msg)
            print(f"  ✗ {msg}")
            return
        
        data = response.json()
        fixtures = data.get("data", [])
        records_fetched = len(fixtures)
        records_upserted = 0
        
        print(f"  Found {records_fetched} live fixtures")
        
        cur = conn.cursor()
        
        for fixture in fixtures:
            # Resolve team and league IDs
            participants = fixture.get("participants", [])
            
            home_team_id = None
            away_team_id = None
            
            for participant in participants:
                meta = participant.get("meta", {})
                location = meta.get("location")
                team_id = participant.get("team_id")
                
                if location == "home":
                    home_team_id = resolver.team(team_id)
                elif location == "away":
                    away_team_id = resolver.team(team_id)
            
            # Skip if teams not found
            if not home_team_id or not away_team_id:
                continue
            
            # Resolve league
            league_id = resolver.league(fixture.get("league_id"))
            if not league_id:
                continue
            
            # Map fixture to game_match columns
            mapped = map_fixture(fixture, home_team_id, away_team_id, league_id)
            
            # Upsert into game_match
            cur.execute("""
                INSERT INTO game_match (
                    external_api_id, league_id, home_team_id, away_team_id,
                    match_datetime, status, home_score, away_score, elapsed_time, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_api_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    elapsed_time = EXCLUDED.elapsed_time,
                    updated_at = NOW();
            """, (
                mapped["external_api_id"],
                mapped["league_id"],
                mapped["home_team_id"],
                mapped["away_team_id"],
                mapped["match_datetime"],
                mapped["status"],
                mapped["home_score"],
                mapped["away_score"],
                mapped["elapsed_time"],
                datetime.now(timezone.utc)
            ))
            
            records_upserted += 1
        
        conn.commit()
        cur.close()
        
        log_sync(conn, "success", 'live_scores', started_at=started_at, records_fetched=records_fetched, records_upserted=records_upserted)
        print(f"  ✓ Synced {records_upserted}/{records_fetched} fixtures")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        if conn:
            conn.rollback() # CRITICAL: Clear aborted transaction state
            log_sync(conn, "failed", 'live_scores', started_at=started_at, error_message=str(e))
    
    finally:
        if conn:
            conn.close()


def sync_fixtures():
    """JOB 2: Sync upcoming fixtures every 6 hours."""
    conn = None
    started_at = datetime.now(timezone.utc)
    
    try:
        conn = get_db_connection()
        resolver = get_resolver()
        
        log_sync(conn, "running", 'fixtures', started_at=started_at)
        print("[SYNC] Fetching upcoming fixtures...")
        
        # Date range: today to today+7days
        today = datetime.now(timezone.utc).date()
        week_later = today + timedelta(days=7)
        
        # Date range: today to today+7days
        today = datetime.now(timezone.utc).date()
        week_later = today + timedelta(days=7)
        
        # 🚀 FIXED: Date ranges are now part of the URL path in V3!
        url = f"{BASE_URL}/fixtures/between/{today}/{week_later}"
        
        # Removed the invalid filter parameter
        params = {
            "include": "participants;state"
        }
        
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            msg = f"API returned {response.status_code}"
            log_sync(conn, "failed", 'fixtures', started_at=started_at, error_message=msg)
            print(f"  ✗ {msg}")
            return
        
        data = response.json()
        fixtures = data.get("data", [])
        records_fetched = len(fixtures)
        records_upserted = 0
        
        print(f"  Found {records_fetched} upcoming fixtures")
        
        cur = conn.cursor()
        
        for fixture in fixtures:
            participants = fixture.get("participants", [])
            
            home_team_id = None
            away_team_id = None
            
            for participant in participants:
                meta = participant.get("meta", {})
                location = meta.get("location")
                team_id = participant.get("team_id")
                
                if location == "home":
                    home_team_id = resolver.team(team_id)
                elif location == "away":
                    away_team_id = resolver.team(team_id)
            
            if not home_team_id or not away_team_id:
                continue
            
            league_id = resolver.league(fixture.get("league_id"))
            if not league_id:
                continue
            
            mapped = map_fixture(fixture, home_team_id, away_team_id, league_id)
            
            # Only update match_datetime and status
            cur.execute("""
                INSERT INTO game_match (
                    external_api_id, league_id, home_team_id, away_team_id,
                    match_datetime, status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_api_id) DO UPDATE SET
                    match_datetime = EXCLUDED.match_datetime,
                    status = EXCLUDED.status,
                    updated_at = NOW();
            """, (
                mapped["external_api_id"],
                mapped["league_id"],
                mapped["home_team_id"],
                mapped["away_team_id"],
                mapped["match_datetime"],
                mapped["status"],
                datetime.now(timezone.utc)
            ))
            
            records_upserted += 1
        
        conn.commit()
        cur.close()
        
        log_sync(conn, "success", 'fixtures', started_at=started_at, records_fetched=records_fetched, records_upserted=records_upserted)
        print(f"  ✓ Synced {records_upserted}/{records_fetched} fixtures")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        if conn:
            conn.rollback() # CRITICAL: Clear aborted transaction state
            log_sync(conn, "failed", 'fixtures', started_at=started_at, error_message=str(e))
    
    finally:
        if conn:
            conn.close()


def sync_player_stats():
    """JOB 3: Sync player stats every 30 minutes."""
    conn = None
    started_at = datetime.now(timezone.utc)
    
    try:
        conn = get_db_connection()
        resolver = get_resolver()
        
        log_sync(conn, "running", 'player_stats', started_at=started_at)
        print("[SYNC] Fetching player stats...")
        
        # Find finished matches with no player stats yet, updated in last 2 hours
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT match_id, external_api_id
            FROM game_match
            WHERE status = 'finished'
            AND updated_at > NOW() - INTERVAL '2 hours'
            AND match_id NOT IN (SELECT match_id FROM player_match_stat);
        """)
        
        matches = cur.fetchall()
        records_fetched = 0
        records_upserted = 0
        
        print(f"  Found {len(matches)} finished matches needing stats")
        
        for match in matches:
            match_id = match["match_id"]
            external_match_id = match["external_api_id"]
            
            # Fetch detailed fixture with player stats
            url = f"{BASE_URL}/fixtures/{external_match_id}"
            params = {"include": "players.statistics.details;players.player"}
            
            response = requests.get(url, headers=HEADERS, params=params)
            
            if response.status_code != 200:
                continue
            
            data = response.json()
            fixture = data.get("data", {})
            players_data = fixture.get("players", [])
            
            records_fetched += len(players_data)
            
            # Process each player's stats
            for player_data in players_data:
                player_obj = player_data.get("player", {})
                player_ext_id = player_obj.get("id")
                
                player_id = resolver.player(player_ext_id)
                if not player_id:
                    continue
                
                mapped_stat = map_player_stat(player_data, player_id, match_id)
                
                # Upsert into player_match_stat
                cur.execute("""
                    INSERT INTO player_match_stat (
                        player_id, match_id, minutes_played, goals, assists,
                        yellow_cards, red_cards, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_id, match_id) DO UPDATE SET
                        minutes_played = EXCLUDED.minutes_played,
                        goals = EXCLUDED.goals,
                        assists = EXCLUDED.assists,
                        yellow_cards = EXCLUDED.yellow_cards,
                        red_cards = EXCLUDED.red_cards,
                        updated_at = NOW();
                """, (
                    mapped_stat["player_id"],
                    mapped_stat["match_id"],
                    mapped_stat["minutes_played"],
                    mapped_stat["goals"],
                    mapped_stat["assists"],
                    mapped_stat["yellow_cards"],
                    mapped_stat["red_cards"],
                    datetime.now(timezone.utc)
                ))
                
                records_upserted += 1
        
        conn.commit()
        cur.close()
        
        log_sync(conn, "success", 'player_stats', started_at=started_at, records_fetched=records_fetched, records_upserted=records_upserted)
        print(f"  ✓ Synced {records_upserted} player stats")
    
    except Exception as e:
        print(f"  ✗ Error: {e}")
        if conn:
            conn.rollback() # CRITICAL: Clear aborted transaction state
            log_sync(conn, "failed", 'player_stats', started_at=started_at, error_message=str(e))
    
    finally:
        if conn:
            conn.close()


def start_scheduler():
    """Create and start the APScheduler BackgroundScheduler."""
    scheduler = BackgroundScheduler(timezone="UTC")
    
    # Add jobs
    scheduler.add_job(sync_live_scores, "interval", seconds=60, id="sync_live_scores")
    scheduler.add_job(sync_fixtures, "interval", hours=6, id="sync_fixtures")
    scheduler.add_job(sync_player_stats, "interval", minutes=30, id="sync_player_stats")
    
    scheduler.start()
    print("✓ APScheduler started with 3 jobs")
    
    return scheduler