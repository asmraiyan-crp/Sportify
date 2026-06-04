"""IDResolver for mapping SportMonks external IDs to database PKs."""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


class IDResolver:
    """Resolves SportMonks external_api_ids to database primary keys."""
    
    def __init__(self, database_url=None):
        """
        Initialize the resolver by loading all mappings from database.
        
        Args:
            database_url: Database connection string (defaults to constructed from env vars)
        """
        if not database_url:
            # Construct from environment variables (same as seed.py)
            database_user = os.getenv("DATABASE_USER", "postgres.pyahykjyflsxnzlzudep")
            database_password = os.getenv("DATABASE_PASSWORD", "QcFDM5kKBO2pE2Qn")
            database_host = os.getenv("DATABASE_HOST", "aws-1-ap-northeast-1.pooler.supabase.com")
            database_port = os.getenv("DATABASE_PORT", "6543")
            database_name = os.getenv("DATABASE_NAME", "postgres")
            
            database_url = f"postgresql://{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"
        
        if not database_url:
            raise ValueError("Database URL could not be constructed")
        
        self._teams = {}
        self._leagues = {}
        self._players = {}
        
        self._load_mappings(database_url)
    
    def _load_mappings(self, database_url):
        """Load all external_api_id -> PK mappings from database."""
        conn = None
        try:
            conn = psycopg2.connect(database_url, sslmode="require")
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Load teams
            cur.execute("SELECT team_id, external_api_id FROM team WHERE external_api_id IS NOT NULL;")
            for row in cur.fetchall():
                self._teams[row["external_api_id"]] = row["team_id"]
            
            # Load leagues
            cur.execute("SELECT league_id, external_api_id FROM league WHERE external_api_id IS NOT NULL;")
            for row in cur.fetchall():
                self._leagues[row["external_api_id"]] = row["league_id"]
            
            # Load players
            cur.execute("SELECT player_id, external_api_id FROM player WHERE external_api_id IS NOT NULL;")
            for row in cur.fetchall():
                self._players[row["external_api_id"]] = row["player_id"]
            
            cur.close()
            print(f"  ✓ Loaded {len(self._teams)} teams, {len(self._leagues)} leagues, {len(self._players)} players")
        
        finally:
            if conn:
                conn.close()
    
    def team(self, ext_id):
        """Resolve team external_api_id to team_id (int) or None."""
        return self._teams.get(str(ext_id))
    
    def league(self, ext_id):
        """Resolve league external_api_id to league_id (int) or None."""
        return self._leagues.get(str(ext_id))
    
    def player(self, ext_id):
        """Resolve player external_api_id to player_id (int) or None."""
        return self._players.get(str(ext_id))
