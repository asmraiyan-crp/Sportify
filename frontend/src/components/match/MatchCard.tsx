import type { Match } from "../../types";
import { StatusBadge } from "../shared";

// ─── Match Card ───────────────────────────────────────────────────────────────

interface MatchCardProps {
  match:   Match;
  onClick: (m: Match) => void;
}

export function MatchCard({ match: m, onClick }: MatchCardProps) {
  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => onClick(m)}
      onKeyDown={e => e.key === "Enter" && onClick(m)}
      className="group relative bg-card border border-border rounded-card px-5 py-[18px] cursor-pointer overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:border-border2 hover:shadow-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      {/* Hover glow */}
      <div className="absolute inset-0 bg-card-glow opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none rounded-card" />

      {/* League + status */}
      <div className="relative z-10 flex items-center justify-between mb-3.5">
        <span className="text-[11.5px] font-medium text-t3 uppercase tracking-widest truncate mr-2">
          {m.league}
        </span>
        <StatusBadge status={m.status} />
      </div>

      {/* Teams + score */}
      <div className="relative z-10 flex items-center">
        <TeamBlock name={m.home.name} badge={m.home.badge} />

        <div className="text-center px-3 shrink-0">
          {m.homeScore !== null ? (
            <>
              <div className="font-display text-[30px] text-t1 tracking-wide whitespace-nowrap">
                {m.homeScore}
                <span className="text-t3 mx-1">:</span>
                {m.awayScore}
              </div>
              <div className="text-[11px] text-live font-semibold mt-1">{m.elapsed}</div>
            </>
          ) : (
            <div className="text-[13px] text-soon font-semibold">
              {m.elapsed ?? "NEXT UP"}
            </div>
          )}
        </div>

        <TeamBlock name={m.away.name} badge={m.away.badge} />
      </div>
    </article>
  );
}

function TeamBlock({ name, badge }: { name: string; badge: string }) {
  return (
    <div className="flex-1 text-center min-w-0">
      <span className="text-[28px] mb-2 block">{badge}</span>
      <div className="font-heading text-sm font-bold text-t1 truncate px-1">{name}</div>
    </div>
  );
}

// ─── Upcoming Row ─────────────────────────────────────────────────────────────

export function UpcomingRow({ match: m }: { match: Match }) {
  return (
    <div className="flex items-center gap-4 bg-card border border-border rounded-lg px-[18px] py-3.5 cursor-pointer transition-all duration-200 hover:border-border2 hover:bg-hover">
      <div className="w-9 h-9 rounded-lg bg-card2 flex items-center justify-center text-base shrink-0">
        {m.home.badge}
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-heading text-[15px] font-bold text-t1 truncate">
          {m.home.name} vs {m.away.name}
        </div>
        <div className="text-[12px] text-t3 mt-0.5">{m.league}</div>
      </div>
      {m.datetime && (
        <div className="text-right shrink-0">
          {m.datetime.includes("·") ? (
            <>
              <div className="text-[12px] text-t2 font-medium">{m.datetime.split("·")[0].trim()}</div>
              <div className="font-heading text-[16px] font-bold text-accent-light">{m.datetime.split("·")[1].trim()}</div>
            </>
          ) : (
            <div className="font-heading text-[14px] font-bold text-accent-light">{m.datetime}</div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Match Modal ──────────────────────────────────────────────────────────────

interface MatchModalProps {
  match:   Match;
  onClose: () => void;
}

export function MatchModal({ match: m, onClose }: MatchModalProps) {
  return (
    <div
      className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm flex items-center justify-center p-6"
      onClick={onClose}
    >
      <div
        className="bg-card border border-border2 rounded-[16px] w-full max-w-[540px] overflow-hidden animate-modal-in"
        onClick={(e: React.MouseEvent) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-border">
          <div>
            <div className="text-[11px] text-t3 uppercase tracking-widest mb-1">
              {m.sport} · {m.league}
            </div>
            <div className="font-heading text-[20px] font-bold text-t1">
              {m.home.name} vs {m.away.name}
            </div>
          </div>
          <button onClick={onClose} aria-label="Close"
            className="w-8 h-8 rounded-md bg-card2 border-none text-t2 text-lg cursor-pointer flex items-center justify-center hover:bg-hover hover:text-t1 transition-all">
            ✕
          </button>
        </div>

        {/* Score */}
        <div className="p-6">
          <div className="text-center py-5">
            <div className="flex items-center justify-center gap-5 mb-3">
              <ModalTeam name={m.home.name} badge={m.home.badge} />
              {m.homeScore !== null ? (
                <div className="text-center">
                  <div className="font-display text-[48px] text-accent-light tracking-wide">
                    {m.homeScore} – {m.awayScore}
                  </div>
                  <div className="text-[13px] text-live font-bold mt-1">⏱ {m.elapsed}</div>
                </div>
              ) : (
                <div className="font-display text-[42px] text-t3">VS</div>
              )}
              <ModalTeam name={m.away.name} badge={m.away.badge} />
            </div>
          </div>

          {/* Meta */}
          <div className="flex justify-center gap-5 mt-2 flex-wrap">
            {[
              { label: "Status", value: m.status.toUpperCase(), cls: m.status === "live" ? "text-live" : m.status === "soon" ? "text-soon" : "text-t1" },
              { label: "Sport",  value: m.sport,  cls: "text-t1" },
              { label: "League", value: m.league, cls: "text-t1" },
              ...(m.venue ? [{ label: "Venue", value: m.venue, cls: "text-t2" }] : []),
            ].map(({ label, value, cls }) => (
              <div key={label} className="text-center">
                <div className="text-[11px] text-t3 uppercase tracking-widest mb-1">{label}</div>
                <div className={`font-heading text-[15px] font-bold ${cls}`}>{value}</div>
              </div>
            ))}
          </div>

          {/* CTAs */}
          <div className="flex gap-2.5 mt-6">
            <button className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-btn text-sm font-semibold bg-accent text-white border-none cursor-pointer font-heading tracking-wide hover:bg-accent-light hover:shadow-accent-glow transition-all duration-200">
              ▶ Watch Live
            </button>
            <button className="flex-1 text-center py-2.5 rounded-btn text-sm font-semibold bg-white/[0.08] text-white border border-white/15 cursor-pointer font-heading tracking-wide hover:bg-white/[0.15] transition-all duration-200">
              📊 Full Stats
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModalTeam({ name, badge }: { name: string; badge: string }) {
  return (
    <div className="text-center">
      <div className="text-[42px] mb-2">{badge}</div>
      <div className="font-heading text-[18px] font-bold text-t1">{name}</div>
    </div>
  );
}
