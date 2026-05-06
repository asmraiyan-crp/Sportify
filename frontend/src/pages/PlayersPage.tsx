import { useState, useEffect } from "react";
import { SPORT_FILTERS } from "../data";
import { PlayerCard } from "../components/player/PlayerCard";
import { SectionHeader, FilterTabs, EmptyState } from "../components/shared";
import { getPlayers } from "../services/playerService";

export function PlayersPage() {
  const [sport, setSport] = useState<string>("All");
  const [players, setPlayers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        setLoading(true);
        const res = await getPlayers({ limit: 100 });
        const transformedPlayers = res.data.map((p: any) => {
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
        setPlayers(transformedPlayers);
      } catch (err: any) {
        console.error("Error fetching players:", err);
        setError(err.message || "Failed to load players");
      } finally {
        setLoading(false);
      }
    };

    fetchPlayers();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚡</div>
        <p className="text-t3">Loading players...</p>
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

  const filtered = sport === "All"
    ? players
    : players.filter(() => {
        // This would filter by sport if the API response includes sport data
        return true;
      });

  return (
    <>
      <SectionHeader title="Top Players" />
      <FilterTabs
        options={SPORT_FILTERS}
        active={sport}
        onChange={(v: string) => setSport(v)}
        className="mb-6"
      />
      {filtered.length > 0 ? (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(170px,1fr))] gap-3 mb-9">
          {filtered.map((p: any) => <PlayerCard key={p.id} player={p} showFollow />)}
        </div>
      ) : (
        <EmptyState message="No players found for this sport." />
      )}
    </>
  );
}
