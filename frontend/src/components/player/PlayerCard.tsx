import type { Player } from "../../types";
import { InjuryBadge } from "../shared";

interface PlayerCardProps {
  player:    Player;
  showFollow?: boolean;
  isFollowed?: boolean;
  onFollow?:   () => void;
}

export function PlayerCard({ player: p, showFollow, isFollowed, onFollow }: PlayerCardProps) {
  return (
    <article className="group bg-card border border-border rounded-card px-4 py-5 text-center cursor-pointer overflow-hidden relative transition-all duration-200 hover:border-accent hover:-translate-y-[3px] hover:shadow-accent-glow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent">

      {/* Avatar */}
      <div className="w-[60px] h-[60px] rounded-full mx-auto mb-3 bg-player-avatar flex items-center justify-center text-[26px] border-2 border-border2 transition-transform duration-200 group-hover:scale-105">
        {p.img}
      </div>

      <div className="font-heading text-[15px] font-bold text-t1 mb-0.5 truncate">{p.name}</div>
      <div className="text-[12px] text-t3 mb-2 truncate">{p.team} · {p.position}</div>

      {/* Rating */}
      <div className="inline-flex items-center gap-1 bg-card2 border border-border2 px-2.5 py-0.5 rounded text-[12px] font-semibold text-soon font-heading mb-2">
        ⭐ {p.rating}
      </div>

      {/* Injury */}
      <div className="flex justify-center mb-2.5">
        <InjuryBadge status={p.injuryStatus} />
      </div>

      {/* Stats */}
      <div className="flex justify-center gap-3.5">
        <PlayerStatBlocks player={p} />
      </div>

      {/* Follow button */}
      {showFollow && (
        <button
          onClick={e => { e.stopPropagation(); onFollow?.(); }}
          className={`mt-3 w-full py-1.5 rounded-btn text-xs font-semibold font-heading tracking-wide border transition-all duration-200
            ${isFollowed
              ? "bg-accent/20 text-accent-light border-accent/40 hover:bg-live/10 hover:text-live hover:border-live/30"
              : "bg-transparent text-t3 border-border hover:border-accent hover:text-accent-light"}`}
        >
          {isFollowed ? "✓ Following" : "+ Follow"}
        </button>
      )}
    </article>
  );
}

// ─── Stat block inside card ───────────────────────────────────────────────────

function StatBlock({ value, label }: { value: number; label: string }) {
  return (
    <div className="text-center">
      <div className="font-heading text-[17px] font-bold text-t1">{value}</div>
      <div className="text-[10px] text-t3 uppercase tracking-wide">{label}</div>
    </div>
  );
}

function PlayerStatBlocks({ player: p }: { player: Player }) {
  const { stats, sport } = p;
  if (sport === "Football") return (
    <>
      {stats.goals   != null && <StatBlock value={stats.goals}   label="Goals"   />}
      {stats.assists != null && <StatBlock value={stats.assists} label="Assists" />}
      {stats.matches != null && <StatBlock value={stats.matches} label="Apps"    />}
    </>
  );
  if (sport === "Cricket") return (
    <>
      {stats.runs    != null && <StatBlock value={stats.runs}    label="Runs"    />}
      {stats.wickets != null && <StatBlock value={stats.wickets} label="Wkts"    />}
      {stats.matches != null && <StatBlock value={stats.matches} label="Matches" />}
    </>
  );
  return <>{stats.matches != null && <StatBlock value={stats.matches} label="Matches" />}</>;
}
