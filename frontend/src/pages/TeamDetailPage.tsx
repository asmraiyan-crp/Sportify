import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { SectionHeader, EmptyState } from "../components/shared";
import { getTeamDetail, getTeamSquad } from "../services/teamService";
import { getMatches } from "../services/matchService";
import { UpcomingRow } from "../components/match/MatchCard";
import type { Team } from "../services/teamService";

export function TeamDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [team, setTeam] = useState<Team | null>(null);
  const [squad, setSquad] = useState<any[]>([]);
  const [fixtures, setFixtures] = useState<any[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState("squad");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchTeamData = async () => {
      if (!id) return;
      try {
        setLoading(true);
        // Fetch team detail
        const teamRes = await getTeamDetail(parseInt(id));
        setTeam(teamRes);

        // Fetch squad
        const squadRes = await getTeamSquad(parseInt(id));
        setSquad(squadRes);

        // Fetch fixtures
        const fixturesRes = await getMatches({ status: "scheduled", limit: 5 });
        setFixtures(fixturesRes.data);

        // Fetch results
        const resultsRes = await getMatches({ status: "finished", limit: 5 });
        setResults(resultsRes.data);
      } catch (err: any) {
        console.error("Error fetching team data:", err);
        setError(err.message || "Failed to load team data");
      } finally {
        setLoading(false);
      }
    };

    fetchTeamData();
  }, [id]);

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚡</div>
        <p className="text-t3">Loading team...</p>
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="text-center py-16">
        <p className="text-live mb-4">⚠️ {error || "Team not found"}</p>
        <button onClick={() => navigate("/teams")} className="text-accent-light hover:underline">
          Back to Teams
        </button>
      </div>
    );
  }

  const tabs = ["squad", "statistics", "fixtures", "results"];

  return (
    <>
      {/* Back button */}
      <button
        onClick={() => navigate("/teams")}
        className="text-accent-light hover:underline mb-6 text-[13px] font-body"
      >
        ← Back to Teams
      </button>

      {/* Team hero banner */}
      <div className="bg-card border border-border rounded-card p-8 mb-8">
        <div className="flex items-start gap-6 mb-6">
          <div className="w-20 h-20 rounded-lg bg-card2 border border-border flex items-center justify-center text-5xl">
            ⚽
          </div>
          <div className="flex-1">
            <h1 className="font-heading text-[36px] font-bold text-t1 mb-2">{team.name}</h1>
            <p className="text-t3 text-[14px] mb-3">
              {team.country || "International"} · {team.founded_year ? `Est. ${team.founded_year}` : ""}
            </p>
            {team.home_ground && <p className="text-t3 text-[13px]">{team.home_ground}</p>}
          </div>
          <button className="px-4 py-2 rounded-btn text-[12px] font-semibold bg-accent text-white border-none cursor-pointer hover:bg-accent-light transition-all">
            + Follow Team
          </button>
        </div>

        {/* Stats row */}
        <div className="flex gap-6 flex-wrap text-[13px]">
          <div>
            <span className="text-t3">League:</span>
            <span className="text-t1 font-semibold ml-2">{team.name}</span>
          </div>
          <div>
            <span className="text-t3">Status:</span>
            <span className="text-t1 font-semibold ml-2">Active</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 text-[13px] font-medium border-b-2 transition-all capitalize
              ${activeTab === tab
                ? "border-accent text-accent-light"
                : "border-transparent text-t3 hover:text-t2"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "squad" && (
        <div>
          <SectionHeader title="Squad" />
          {squad.length > 0 ? (
            <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3 mb-9">
              {squad.map((player: any) => (
                <div
                  key={player.id}
                  className="bg-card border border-border rounded-card p-4 hover:border-border2 transition-all"
                >
                  <div className="text-center mb-3">
                    <div className="text-3xl mb-2">⚽</div>
                    <h3 className="font-heading text-[14px] font-bold text-t1">{player.name}</h3>
                  </div>
                  <div className="text-center text-[12px] text-t3 space-y-1">
                    <p>{player.position || "N/A"}</p>
                    {player.jersey_number && <p>#{player.jersey_number}</p>}
                    {player.injury_status && (
                      <p className={player.injury_status === "active" ? "text-accent-light" : "text-live"}>
                        {player.injury_status}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon="⚽" message="No squad data available." />
          )}
        </div>
      )}

      {activeTab === "statistics" && (
        <div>
          <SectionHeader title="Statistics" />
          <div className="grid md:grid-cols-2 gap-6 mb-9">
            <div className="bg-card border border-border rounded-card p-6">
              <h3 className="font-heading text-[16px] font-bold text-t1 mb-4">Season Stats</h3>
              <div className="space-y-3 text-[13px]">
                <div className="flex justify-between">
                  <span className="text-t3">Goals Scored:</span>
                  <span className="font-semibold text-t1">56</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-t3">Goals Conceded:</span>
                  <span className="font-semibold text-t1">24</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-t3">Clean Sheets:</span>
                  <span className="font-semibold text-t1">9</span>
                </div>
              </div>
            </div>
            <div className="bg-card border border-border rounded-card p-6">
              <h3 className="font-heading text-[16px] font-bold text-t1 mb-4">Performance</h3>
              <div className="space-y-3 text-[13px]">
                <div className="flex justify-between">
                  <span className="text-t3">Matches Played:</span>
                  <span className="font-semibold text-t1">27</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-t3">Wins:</span>
                  <span className="font-semibold text-accent-light">18</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-t3">Position:</span>
                  <span className="font-semibold text-t1">#1</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "fixtures" && (
        <div>
          <SectionHeader title="Upcoming Fixtures" />
          {fixtures.length > 0 ? (
            <div className="flex flex-col gap-2 mb-9">
              {fixtures.map((match: any) => <UpcomingRow key={match.id} match={match} />)}
            </div>
          ) : (
            <EmptyState icon="📅" message="No upcoming fixtures." />
          )}
        </div>
      )}

      {activeTab === "results" && (
        <div>
          <SectionHeader title="Recent Results" />
          {results.length > 0 ? (
            <div className="flex flex-col gap-2 mb-9">
              {results.map((match: any) => <UpcomingRow key={match.id} match={match} />)}
            </div>
          ) : (
            <EmptyState icon="📊" message="No results available." />
          )}
        </div>
      )}
    </>
  );
}
