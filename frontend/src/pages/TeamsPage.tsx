import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { SectionHeader, EmptyState } from "../components/shared";
import { getTeams } from "../services/teamService";
import type { Team } from "../services/teamService";

export function TeamsPage() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<Team[]>([]);
  const [filteredTeams, setFilteredTeams] = useState<Team[]>([]);
  const [search, setSearch] = useState("");
  const [sport, setSport] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const res = await getTeams({ limit: 100 });
        setTeams(res.data);
      } catch (err: any) {
        console.error("Error fetching teams:", err);
        setError(err.message || "Failed to load teams");
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  useEffect(() => {
    let filtered = teams;

    if (search) {
      filtered = filtered.filter(t => t.name.toLowerCase().includes(search.toLowerCase()));
    }

    if (sport !== "All") {
      // Filter by sport if needed
      // For now, just show all teams regardless of sport selection
    }

    setFilteredTeams(filtered);
  }, [teams, search, sport]);

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚡</div>
        <p className="text-t3">Loading teams...</p>
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
      <SectionHeader title="Teams" />
      
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search teams..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-2.5 bg-card border border-border rounded-lg text-[13px] font-body text-t1 placeholder:text-t3 focus:outline-none focus:border-accent transition-colors"
        />
      </div>

      <div className="flex gap-1.5 mb-6 flex-wrap">
        {["All", "Football", "Cricket"].map(s => (
          <button
            key={s}
            onClick={() => setSport(s)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium cursor-pointer font-body transition-all duration-200
              ${sport === s
                ? "bg-accent/20 border border-accent/50 text-accent-light"
                : "bg-card border border-border text-t2 hover:border-border2 hover:text-t1"}`}
          >
            {s === "Football" ? "⚽" : s === "Cricket" ? "🏏" : "🏆"}
            {s}
          </button>
        ))}
      </div>

      {filteredTeams.length > 0 ? (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4 mb-9">
          {filteredTeams.map(team => (
            <div
              key={team.id}
              className="bg-card border border-border rounded-card p-4 hover:border-border2 hover:shadow-md transition-all duration-200 cursor-pointer"
              onClick={() => navigate(`/teams/${team.id}`)}
            >
              <div className="w-16 h-16 rounded-lg bg-card2 border border-border flex items-center justify-center text-3xl mb-3">
                {(team as any).logo_url ? (
                  <img src={(team as any).logo_url} alt={team.name} className="w-full h-full object-cover rounded" />
                ) : (
                  "⚽"
                )}
              </div>
              <h3 className="font-heading text-[15px] font-bold text-t1 mb-1">{team.name}</h3>
              <p className="text-[12px] text-t3 mb-2">{team.country || "International"}</p>
              {team.founded_year && (
                <p className="text-[11px] text-t3">Founded: {team.founded_year}</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState icon="⚽" message="No teams found." />
      )}
    </>
  );
}
