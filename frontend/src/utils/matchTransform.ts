/**
 * Transform raw API match response to component-expected format
 */
export function transformMatch(m: any) {
  return {
    ...m,
    id: m.match_id || m.id,
    home: {
      name: m.home_team?.name || "Unknown",
      badge: m.league?.sport?.name === "Cricket" ? "🏏" : "⚽",
    },
    away: {
      name: m.away_team?.name || "Unknown",
      badge: m.league?.sport?.name === "Cricket" ? "🏏" : "⚽",
    },
    homeScore: m.home_score,
    awayScore: m.away_score,
    elapsed: m.elapsed_time,
    league: m.league?.name || "Unknown",
  };
}

export function transformMatches(matches: any[]): any[] {
  return (matches || []).map(transformMatch);
}
