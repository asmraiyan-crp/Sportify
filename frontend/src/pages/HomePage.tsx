import { useState, useEffect } from "react";
import type { Match } from "../types";
import { HERO_SLIDES, SPORT_FILTERS } from "../data";
import { useMatchFilter, useModal } from "../hooks";
import { HeroSlider }     from "../components/hero/HeroSlider";
import { MatchCard, UpcomingRow, MatchModal } from "../components/match/MatchCard";
import { PlayerCard }     from "../components/player/PlayerCard";
import { StandingsTable } from "../components/standings/StandingsTable";
import { SectionHeader, FilterTabs, EmptyState } from "../components/shared";
import { getLiveMatches, getMatches } from "../services/matchService";
import { getPlayers } from "../services/playerService";
import { getLeagueStandings } from "../services/leagueService";

export function HomePage() {
  const [liveMatches, setLiveMatches] = useState<any[]>([]);
  const [upcomingMatches, setUpcomingMatches] = useState<any[]>([]);
  const [topPlayers, setTopPlayers] = useState<any[]>([]);
  const [standings, setStandings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  const matchFilter = useMatchFilter(liveMatches);
  const modal = useModal<Match>();
  const { sport, setSport, filtered } = matchFilter;

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch live matches
        const liveRes = await getLiveMatches();
        setLiveMatches(liveRes);

        // Fetch upcoming matches
        const upcomingRes = await getMatches({ status: "scheduled", limit: 5 });
        setUpcomingMatches(upcomingRes.data);

        // Fetch top players
        const playersRes = await getPlayers({ limit: 6 });
        const transformedPlayers = playersRes.data.map((p: any) => {
          const injuryMap: { [key: string]: any } = {
            "fit": "fit",
            "injured": "injured",
            "doubtful": "doubtful",
          };
          return {
            id: p.id || p.player_id,
            name: p.name,
            team: p.team?.name || "Unknown",
            teamId: p.team_id,
            sport: "Football" as const,
            position: p.position_role || p.position || "Unknown",
            rating: 4.5,
            injuryStatus: (injuryMap[p.injury_status] || "fit") as any,
            img: "⚽",
            stats: {
              goals: 0,
              assists: 0,
              matches: 0,
            }
          };
        });
        setTopPlayers(transformedPlayers);

        // Fetch standings for league 2
        const standingsRes = await getLeagueStandings(2);
        setStandings(standingsRes.data);
      } catch (err: any) {
        console.error("Error fetching home page data:", err);
        setError(err.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚡</div>
        <p className="text-t3">Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-live mb-4">⚠️ {error}</p>
        <button onClick={() => window.location.reload()} className="text-accent-light hover:underline">
          Try again
        </button>
      </div>
    );
  }

  return (
    <>
      <HeroSlider slides={HERO_SLIDES} />

      <FilterTabs
        options={SPORT_FILTERS}
        active={sport}
        onChange={(v: string) => setSport(v as any)}
        className="mb-5"
      />

      <SectionHeader title="Live Matches" linkText="See All" />
      {filtered.length > 0 ? (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3 mb-9">
          {filtered.map((m: Match) => (
            <MatchCard key={m.id} match={m} onClick={modal.open} />
          ))}
        </div>
      ) : (
        <EmptyState icon="🏟️" message="No live matches for this sport right now." />
      )}

      <SectionHeader title="Upcoming Fixtures" linkText="Full Schedule" />
      <div className="flex flex-col gap-2 mb-9">
        {upcomingMatches.length > 0 ? (
          upcomingMatches.map((m: any) => <UpcomingRow key={m.id} match={m} />)
        ) : (
          <EmptyState icon="📅" message="No upcoming matches." />
        )}
      </div>

      {/* 2-col: standings + players */}
      <div className="grid lg:grid-cols-2 gap-8 mb-9">
        <div>
          <SectionHeader title="PL Standings" linkText="Full Table" />
          <div className="bg-card border border-border rounded-card p-4 overflow-x-auto">
            {standings.length > 0 ? (
              <StandingsTable rows={standings.slice(0, 5)} compact />
            ) : (
              <EmptyState icon="📊" message="No standings data available." />
            )}
          </div>
        </div>
        <div>
          <SectionHeader title="Top Players" linkText="All Players" />
          <div className="grid grid-cols-2 gap-3">
            {topPlayers.length > 0 ? (
              topPlayers.slice(0, 4).map((p: any) => (
                <PlayerCard key={p.id} player={p} />
              ))
            ) : (
              <EmptyState icon="⚽" message="No players data available." />
            )}
          </div>
        </div>
      </div>

      {modal.item && <MatchModal match={modal.item} onClose={modal.close} />}
    </>
  );
}
