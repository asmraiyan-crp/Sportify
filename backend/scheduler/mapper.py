"""SportMonks fixture and player stat mappers."""

STATUS_MAP = {
    "NS": "scheduled",
    "INPLAY_1ST_HALF": "live",
    "INPLAY_2ND_HALF": "live",
    "HT": "live",
    "INPLAY_ET": "live",
    "INPLAY_PENALTIES": "live",
    "FT": "finished",
    "AET": "finished",
    "PEN_BREAK": "finished",
    "POSTP": "postponed",
    "CANCL": "cancelled",
    "TBA": "scheduled",
}


def map_fixture(fixture, home_team_id, away_team_id, league_id):
    """
    Map a SportMonks fixture to game_match columns.
    
    Args:
        fixture: Raw fixture data from SportMonks API
        home_team_id: Resolved home team PK
        away_team_id: Resolved away team PK
        league_id: Resolved league PK
    
    Returns:
        dict with game_match columns
    """
    fixture_id = fixture.get("id")
    
    # Parse scores array for CURRENT home/away goals
    scores = fixture.get("scores", [])
    home_score = 0
    away_score = 0
    
    for score in scores:
        if score.get("type") == "CURRENT":
            home_score = score.get("score", {}).get("home", 0) or 0
            away_score = score.get("score", {}).get("away", 0) or 0
            break
    
    # Parse periods array for elapsed minutes
    periods = fixture.get("periods", [])
    elapsed_time = 0
    
    for period in periods:
        if period.get("minute"):
            elapsed_time = period.get("minute", 0)
    
    # Parse state for status
    state = fixture.get("state", {})
    state_type = state.get("type", "NS")
    status = STATUS_MAP.get(state_type, "scheduled")
    
    # Match datetime
    match_datetime = fixture.get("starting_at")
    
    return {
        "external_api_id": str(fixture_id),
        "league_id": league_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "match_datetime": match_datetime,
        "status": status,
        "home_score": home_score,
        "away_score": away_score,
        "elapsed_time": elapsed_time,
    }


def map_player_stat(stat_data, player_id, match_id):
    """
    Map SportMonks player statistics to player_match_stat columns.
    
    Args:
        stat_data: Raw player stats from SportMonks API fixture
        player_id: Resolved player PK
        match_id: Resolved match PK
    
    Returns:
        dict with player_match_stat columns
    """
    details = stat_data.get("statistics", {}).get("details", [])
    
    # Initialize stats
    stats = {
        "player_id": player_id,
        "match_id": match_id,
        "minutes_played": 0,
        "goals": 0,
        "assists": 0,
        "yellow_cards": 0,
        "red_cards": 0,
    }
    
    # Parse details array
    for detail in details:
        detail_type = detail.get("type", {}).get("developer_name", "")
        value = detail.get("value", 0)
        
        if detail_type == "MINUTES_PLAYED":
            stats["minutes_played"] = int(value) if value else 0
        elif detail_type == "GOALS":
            stats["goals"] = int(value) if value else 0
        elif detail_type == "GOAL_ASSIST":
            stats["assists"] = int(value) if value else 0
        elif detail_type == "YELLOWCARD":
            stats["yellow_cards"] = int(value) if value else 0
        elif detail_type == "REDCARD":
            stats["red_cards"] = int(value) if value else 0
    
    return stats
