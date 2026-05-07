import { useState, useEffect } from "react";
import type { Match, SportFilter } from "../types";
import { SPORT_FILTERS } from "../data";
import { useMatchFilter, useModal } from "../hooks";
import { MatchCard, UpcomingRow, MatchModal } from "../components/match/MatchCard";
import { SectionHeader, FilterTabs, EmptyState } from "../components/shared";
import { getLiveMatches, getMatches } from "../services/matchService";
import { transformMatches } from "../utils/matchTransform";

export function MatchesPage() {
  const [liveMatches, setLiveMatches] = useState<any[]>([]);
  const [scheduledMatches, setScheduledMatches] = useState<any[]>([]);
  const [finishedMatches, setFinishedMatches] = useState<any[]>([]);
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
        setLiveMatches(transformMatches(liveRes));

        // Fetch scheduled matches
        const scheduledRes = await getMatches({ status: "scheduled" });
        setScheduledMatches(transformMatches(scheduledRes.data));

        // Fetch finished matches
        const finishedRes = await getMatches({ status: "finished" });
        setFinishedMatches(transformMatches(finishedRes.data));
      } catch (err: any) {
        console.error("Error fetching matches:", err);
        setError(err.message || "Failed to load matches");
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
        <p className="text-t3">Loading matches...</p>
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

  const filteredLive = filtered.filter((m: Match) => m.status === "live");
  const filteredScheduled = scheduledMatches.filter((m: any) => {
    if (sport === "All") return true;
    return m.league === sport || m.league_name === sport;
  });

  return (
    <>
      <SectionHeader title="Matches" />
      
      <FilterTabs
        options={SPORT_FILTERS}
        active={sport}
        onChange={(v: string) => setSport(v as SportFilter)}
        className="mb-6"
      />

      {filteredLive.length > 0 && (
        <>
          <SectionHeader title="Live Now" />
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3 mb-8">
            {filteredLive.map((m: any) => <MatchCard key={m.id} match={m} onClick={modal.open} />)}
          </div>
        </>
      )}

      <SectionHeader title="Upcoming Fixtures" />
      {filteredScheduled.length > 0 ? (
        <div className="flex flex-col gap-2 mb-9">
          {filteredScheduled.map((m: any) => <UpcomingRow key={m.id} match={m} />)}
        </div>
      ) : (
        <EmptyState message="No upcoming fixtures for this sport." />
      )}

      {finishedMatches.length > 0 && (
        <>
          <SectionHeader title="Recent Results" />
          <div className="flex flex-col gap-2 mb-9">
            {finishedMatches.slice(0, 5).map((m: any) => <UpcomingRow key={m.id} match={m} />)}
          </div>
        </>
      )}

      {modal.item && <MatchModal match={modal.item} onClose={modal.close} />}
    </>
  );
}
