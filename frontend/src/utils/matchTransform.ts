/**
 * Transform raw API match response to component-expected format
 */
export function transformMatch(m: any) {
  // Determine sport type from league_name or venue
  const leagueName = m.league_name || m.league?.name || "Unknown";
  const isCricket = leagueName.includes("Premier League") || 
                    leagueName.includes("IPL") || 
                    leagueName.includes("Big Bash") ||
                    m.venue?.includes("Cricket") ||
                    m.league?.sport?.name === "Cricket";
  const badge = isCricket ? "🏏" : "⚽";
  
  return {
    ...m,
    id: m.match_id || m.id,
    home: {
      name: m.home_team_name || m.home_team?.name || "Unknown",
      badge,
    },
    away: {
      name: m.away_team_name || m.away_team?.name || "Unknown",
      badge,
    },
    homeScore: m.home_score,
    awayScore: m.away_score,
    elapsed: m.elapsed_time,
    league: leagueName,
  };
}

export function transformMatches(matches: any[]): any[] {
  return (matches || []).map(transformMatch);
}
