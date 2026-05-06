import { useState, useEffect } from "react";
import { SPORT_FILTERS } from "../data";
import { PlayerCard } from "../components/player/PlayerCard";
import { SectionHeader, FilterTabs, EmptyState } from "../components/shared";
import { getPlayers } from "../services/playerService";

export function PlayersPage() {
  const [sport, setSport] = useState<string>("All");
  const [search, setSearch] = useState<string>("");
  const [players, setPlayers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        setLoading(true);
        // Fetch players filtered by sport via API
        const params: any = { limit: 100 };
        if (sport !== "All") {
          params.sport_name = sport;
        }
        const res = await getPlayers(params);
        const transformedPlayers = res.data.map((p: any) => {
          const injuryMap: { [key: string]: any } = {
            "fit": "fit",
            "injured": "injured",
            "doubtful": "doubtful",
          };
          const sportIcon = p.sport?.name === "Cricket" ? "🏏" : "⚽";
          return {
            id: p.id || p.player_id,
            name: p.name,
            team: p.team?.name || "Unknown",
            teamId: p.team_id,
            sport: p.sport?.name || "Football",
            position: p.position_role || p.position || "Unknown",
            rating: 4.5,
            injuryStatus: (injuryMap[p.injury_status] || "fit") as any,
            img: sportIcon,
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
  }, [sport]);

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

  const filtered = players.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <>
      <SectionHeader title="Top Players" />
      
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search players by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-[13px] font-body text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
        />
      </div>

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
        <EmptyState message={search ? "No players found matching your search." : "No players found for this sport."} />
      )}
    </>
  );
}
