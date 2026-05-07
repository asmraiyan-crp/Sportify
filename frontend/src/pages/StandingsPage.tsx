import { useState, useEffect } from "react";
import { StandingsTable } from "../components/standings/StandingsTable";
import { SectionHeader, EmptyState } from "../components/shared";
import { getLeagues, getLeagueStandings } from "../services/leagueService";
import type { League } from "../services/leagueService";
import type { Standing } from "../types";

// Helper to get league ID from League object
function getLeagueId(league: League): number {
  return league.league_id || league.id || 0;
}

// Transform API response to component Standing format
function transformStanding(s: any): Standing {
  return {
    pos: s.pos,
    team: s.team_name || "Unknown",
    badge: s.league_name?.includes("IPL") || s.league_name?.includes("Big Bash") || s.league_name?.includes("Premier") ? "🏏" : "⚽",
    played: s.played,
    won: s.won,
    drawn: s.drawn,
    lost: s.lost,
    gf: s.gf,
    ga: s.ga,
    pts: s.pts,
    form: [], // Generate form based on recent matches if available
  };
}

export function StandingsPage() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [activeLeague, setActiveLeague] = useState<League | null>(null);
  const [standings, setStandings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchLeagues = async () => {
      try {
        setLoading(true);
        const res = await getLeagues();
        if (res.data.length > 0) {
          setLeagues(res.data);
          setActiveLeague(res.data[0]);
        }
      } catch (err: any) {
        console.error("Error fetching leagues:", err);
        setError(err.message || "Failed to load leagues");
      } finally {
        setLoading(false);
      }
    };

    fetchLeagues();
  }, []);

  useEffect(() => {
    if (activeLeague) {
      const fetchStandings = async () => {
        try {
          const leagueId = getLeagueId(activeLeague);
          const res = await getLeagueStandings(leagueId);
          // Transform API response to component format
          const transformed = (res.data || []).map(transformStanding);
          setStandings(transformed);
        } catch (err: any) {
          console.error("Error fetching standings:", err);
          setStandings([]);
        }
      };

      fetchStandings();
    }
  }, [activeLeague]);

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚡</div>
        <p className="text-t3">Loading standings...</p>
      </div>
    );
  }

  if (error || leagues.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-live mb-4">⚠️ {error || "No leagues found"}</p>
        <button onClick={() => window.location.reload()} className="text-accent-light hover:underline">
          Try again
        </button>
      </div>
    );
  }

  return (
    <>
      <SectionHeader title="League Standings" />

      <div className="flex gap-1.5 mb-6 flex-wrap">
        {leagues.map((l: League) => (
          <button
            key={getLeagueId(l)}
            onClick={() => setActiveLeague(l)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium cursor-pointer font-body transition-all duration-200
              ${getLeagueId(activeLeague!) === getLeagueId(l)
                ? "bg-accent/20 border border-accent/50 text-accent-light"
                : "bg-card border border-border text-t2 hover:border-border2 hover:text-t1"}`}
          >
            <span>{l.sport_id === 1 ? "⚽" : "🏏"}</span>
            {l.name}
          </button>
        ))}
      </div>

      <div className="bg-card border border-border rounded-card p-5 overflow-x-auto mb-9">
        {activeLeague && (
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <span className="text-xl">{activeLeague.sport_id === 1 ? "⚽" : "🏏"}</span>
              <span className="font-heading text-[17px] font-bold text-t1">{activeLeague.name}</span>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-t3 font-body">
              <span className="w-2 h-2 rounded-full bg-accent-light inline-block" /> Top 4
              <span className="w-2 h-2 rounded-full bg-live inline-block ml-2" /> Relegation
            </div>
          </div>
        )}
        {standings.length > 0 ? (
          <StandingsTable rows={standings} />
        ) : (
          <EmptyState icon="📊" message="No standings data available yet." />
        )}
      </div>
    </>
  );
}
