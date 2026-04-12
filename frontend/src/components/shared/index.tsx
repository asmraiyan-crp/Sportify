import type { HeroTag, FormResult, InjuryStatus } from "../../types";

// ─── Hero Badge ───────────────────────────────────────────────────────────────

const BADGE: Record<HeroTag, string> = {
  LIVE:     "bg-live/10 text-live border border-live/30",
  TRENDING: "bg-accent/10 text-accent-light border border-accent/30",
  WATCH:    "bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/30",
};

export function HeroBadge({ tag, className = "" }: { tag: HeroTag; className?: string }) {
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-bold tracking-widest font-heading ${BADGE[tag]} ${className}`}>
      {tag === "LIVE" && <span className="w-1.5 h-1.5 rounded-full bg-live animate-pulse2 inline-block" />}
      {tag}
    </div>
  );
}

// ─── Status Badge ─────────────────────────────────────────────────────────────

export function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const cls =
    s === "live"     ? "bg-live/10 text-live border-live/25"   :
    s === "soon"     ? "bg-soon/10 text-soon border-soon/25"   :
    s === "finished" ? "bg-t3/10 text-t3 border-t3/20"        :
                       "bg-t3/10 text-t3 border-t3/20";
  const label =
    s === "live" ? "● LIVE" : s === "soon" ? "SOON" : s === "finished" ? "FT" : "SCHED";
  return (
    <span className={`text-[10.5px] font-bold tracking-widest px-2 py-0.5 rounded font-heading border ${cls}`}>
      {label}
    </span>
  );
}

// ─── Injury Badge ─────────────────────────────────────────────────────────────

const INJURY_DOT: Record<InjuryStatus, string>   = { fit:"bg-win",    injured:"bg-live",  doubtful:"bg-soon" };
const INJURY_LABEL: Record<InjuryStatus, string> = { fit:"Fit",       injured:"Injured",  doubtful:"Doubtful" };
const INJURY_TEXT: Record<InjuryStatus, string>  = { fit:"text-win",  injured:"text-live",doubtful:"text-soon" };

export function InjuryBadge({ status }: { status: InjuryStatus }) {
  return (
    <div className="flex items-center gap-1">
      <span className={`w-1.5 h-1.5 rounded-full ${INJURY_DOT[status]}`} />
      <span className={`text-[10px] font-semibold uppercase tracking-wide ${INJURY_TEXT[status]}`}>
        {INJURY_LABEL[status]}
      </span>
    </div>
  );
}

// ─── Form Dots ────────────────────────────────────────────────────────────────

const FORM_COLOR: Record<FormResult, string> = { W:"bg-win", D:"bg-soon", L:"bg-live" };

export function FormDots({ form }: { form: FormResult[] }) {
  return (
    <div className="flex items-center gap-0.5">
      {form.map((f, i) => (
        <div key={i} title={f} className={`w-1.5 h-1.5 rounded-full ${FORM_COLOR[f]}`} />
      ))}
    </div>
  );
}

// ─── Section Header ───────────────────────────────────────────────────────────

interface SectionHeaderProps {
  title:     string;
  linkText?: string;
  onLink?:   () => void;
}
export function SectionHeader({ title, linkText, onLink }: SectionHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="flex items-center gap-2.5 font-heading text-[18px] font-bold text-t1">
        <span className="w-[3px] h-[18px] rounded-sm bg-accent-bar shrink-0 inline-block" />
        {title}
      </h2>
      {linkText && (
        <button
          onClick={onLink}
          className="text-[12.5px] text-accent-light cursor-pointer hover:text-purple-300 transition-colors duration-150 bg-transparent border-none font-body"
        >
          {linkText} →
        </button>
      )}
    </div>
  );
}

// ─── Filter Tabs ──────────────────────────────────────────────────────────────

interface FilterTabsProps {
  options:    string[];
  active:     string;
  onChange:   (v: string) => void;
  className?: string;
}
export function FilterTabs({ options, active, onChange, className = "" }: FilterTabsProps) {
  return (
    <div className={`flex gap-1.5 flex-wrap ${className}`}>
      {options.map(opt => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          className={`px-4 py-1.5 rounded-md text-[13px] font-medium cursor-pointer font-body transition-all duration-200
            ${active === opt
              ? "bg-accent border border-accent text-white"
              : "bg-card border border-border text-t2 hover:border-accent hover:text-t1"}`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

// ─── Empty State ──────────────────────────────────────────────────────────────

export function EmptyState({ icon = "🏟️", message }: { icon?: string; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-14 text-center text-t3">
      <span className="text-4xl mb-3">{icon}</span>
      <p className="text-[14px] font-body">{message}</p>
    </div>
  );
}

// ─── Divider Label ────────────────────────────────────────────────────────────

export function DividerLabel({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 mb-3.5">
      <span className="font-heading text-[13px] font-bold text-t3 uppercase tracking-widest whitespace-nowrap">
        {label}
      </span>
      <div className="flex-1 h-px bg-border" />
    </div>
  );
}

// ─── Capacity Bar ─────────────────────────────────────────────────────────────

export function CapacityBar({ registered, capacity }: { registered: number; capacity: number }) {
  const pct   = Math.min(100, Math.round((registered / capacity) * 100));
  const color = pct >= 90 ? "bg-live" : pct >= 60 ? "bg-soon" : "bg-accent";
  return (
    <div>
      <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-[11px] text-t3">{pct}% full</span>
        <span className="text-[11px] text-t3">{capacity - registered} spots left</span>
      </div>
    </div>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`bg-border2 rounded animate-pulse ${className}`} />;
}

export function MatchCardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-card p-5 animate-pulse">
      <div className="flex justify-between mb-3.5">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-5 w-12" />
      </div>
      <div className="flex items-center justify-between">
        <div className="flex-1 flex flex-col items-center gap-2">
          <Skeleton className="w-9 h-9 rounded-full" />
          <Skeleton className="h-3 w-16" />
        </div>
        <div className="flex flex-col items-center gap-1 px-3">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-2.5 w-12" />
        </div>
        <div className="flex-1 flex flex-col items-center gap-2">
          <Skeleton className="w-9 h-9 rounded-full" />
          <Skeleton className="h-3 w-16" />
        </div>
      </div>
    </div>
  );
}

// ─── Stat Pill ────────────────────────────────────────────────────────────────

export function StatPill({
  value, label, accent = false,
}: {
  value:   string | number;
  label:   string;
  accent?: boolean;
}) {
  return (
    <div className={`flex flex-col items-center px-3 py-2 rounded-lg border ${accent ? "bg-accent/10 border-accent/30" : "bg-card2 border-border"}`}>
      <span className={`font-heading text-[18px] font-bold ${accent ? "text-accent-light" : "text-t1"}`}>{value}</span>
      <span className="text-[10px] text-t3 uppercase tracking-wide">{label}</span>
    </div>
  );
}
