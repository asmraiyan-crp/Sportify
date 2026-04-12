import { useState } from "react";
import type { Match, FanEvent, SportFilter } from "../types";
import {
  HERO_SLIDES, LIVE_MATCHES, UPCOMING_MATCHES, TOP_PLAYERS,
  PL_STANDINGS, FAN_EVENTS, SPORT_FILTERS,
} from "../data";
import { useMatchFilter, useModal } from "../hooks";
import { HeroSlider }     from "../components/hero/HeroSlider";
import { MatchCard, UpcomingRow, MatchModal } from "../components/match/MatchCard";
import { PlayerCard }     from "../components/player/PlayerCard";
import { StandingsTable } from "../components/standings/StandingsTable";
import { SectionHeader, FilterTabs, EmptyState, CapacityBar } from "../components/shared";

// ─── Local league type ────────────────────────────────────────────────────────

interface League {
  id:    number;
  name:  string;
  flag:  string;
  sport: string;
}

const LEAGUES: League[] = [
  { id: 1, name: "Premier League", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", sport: "Football" },
  { id: 2, name: "La Liga",        flag: "🇪🇸",         sport: "Football" },
  { id: 3, name: "UCL",            flag: "🇪🇺",         sport: "Football" },
  { id: 4, name: "IPL 2025",       flag: "🇮🇳",         sport: "Cricket"  },
];

// ─── Shared tab props ─────────────────────────────────────────────────────────

interface TabProps {
  matchFilter: ReturnType<typeof useMatchFilter>;
  modal:       ReturnType<typeof useModal<Match>>;
}

// ─── Dashboard Page ───────────────────────────────────────────────────────────

export function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"home" | "matches" | "standings" | "players" | "events">("home");
  const matchFilter = useMatchFilter(LIVE_MATCHES);
  const modal       = useModal<Match>();

  return (
    <>
      {/* Tab sub-nav */}
      <div className="flex gap-1 mb-6 border-b border-border pb-0 -mt-2">
        {(["home","matches","standings","players","events"] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-[13px] font-medium font-body capitalize transition-all duration-150 border-none cursor-pointer border-b-2 -mb-px
              ${activeTab === tab
                ? "text-t1 border-accent bg-transparent"
                : "text-t3 border-transparent bg-transparent hover:text-t2"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "home"      && <HomeTab      matchFilter={matchFilter} modal={modal} />}
      {activeTab === "matches"   && <MatchesTab   matchFilter={matchFilter} modal={modal} />}
      {activeTab === "standings" && <StandingsTab />}
      {activeTab === "players"   && <PlayersTab />}
      {activeTab === "events"    && <EventsTab />}

      {modal.item && <MatchModal match={modal.item} onClose={modal.close} />}
    </>
  );
}

// ─── Home Tab ─────────────────────────────────────────────────────────────────

function HomeTab({ matchFilter, modal }: TabProps) {
  const { sport, setSport, filtered } = matchFilter;

  return (
    <>
      <HeroSlider slides={HERO_SLIDES} />

      <FilterTabs
        options={SPORT_FILTERS}
        active={sport}
        onChange={(v: string) => setSport(v as SportFilter)}
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
        {UPCOMING_MATCHES.map((m: Match) => <UpcomingRow key={m.id} match={m} />)}
      </div>

      {/* 2-col: standings + players */}
      <div className="grid lg:grid-cols-2 gap-8 mb-9">
        <div>
          <SectionHeader title="PL Standings" linkText="Full Table" />
          <div className="bg-card border border-border rounded-card p-4 overflow-x-auto">
            <StandingsTable rows={PL_STANDINGS.slice(0, 5)} compact />
          </div>
        </div>
        <div>
          <SectionHeader title="Top Players" linkText="All Players" />
          <div className="grid grid-cols-2 gap-3">
            {TOP_PLAYERS.slice(0, 4).map(p => (
              <PlayerCard key={p.id} player={p} />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Matches Tab ──────────────────────────────────────────────────────────────

function MatchesTab({ matchFilter, modal }: TabProps) {
  const { sport, setSport, filtered } = matchFilter;
  const live      = filtered.filter((m: Match) => m.status === "live");
  const soon      = filtered.filter((m: Match) => m.status === "soon");
  const scheduled = UPCOMING_MATCHES.filter((m: Match) =>
    sport === "All" || m.sport === sport
  );

  return (
    <>
      <FilterTabs
        options={SPORT_FILTERS}
        active={sport}
        onChange={(v: string) => setSport(v as SportFilter)}
        className="mb-6"
      />

      {live.length > 0 && (
        <>
          <SectionHeader title="Live Now" />
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3 mb-8">
            {live.map((m: Match) => <MatchCard key={m.id} match={m} onClick={modal.open} />)}
          </div>
        </>
      )}

      {soon.length > 0 && (
        <>
          <SectionHeader title="Starting Soon" />
          <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3 mb-8">
            {soon.map((m: Match) => <MatchCard key={m.id} match={m} onClick={modal.open} />)}
          </div>
        </>
      )}

      <SectionHeader title="Upcoming Fixtures" />
      {scheduled.length > 0 ? (
        <div className="flex flex-col gap-2 mb-9">
          {scheduled.map((m: Match) => <UpcomingRow key={m.id} match={m} />)}
        </div>
      ) : (
        <EmptyState message="No upcoming fixtures for this sport." />
      )}
    </>
  );
}

// ─── Standings Tab ────────────────────────────────────────────────────────────

function StandingsTab() {
  const [activeLeague, setActiveLeague] = useState<League>(LEAGUES[0]);

  return (
    <>
      <SectionHeader title="League Standings" />

      <div className="flex gap-1.5 mb-6 flex-wrap">
        {LEAGUES.map((l: League) => (
          <button
            key={l.id}
            onClick={() => setActiveLeague(l)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-medium cursor-pointer font-body transition-all duration-200
              ${activeLeague.id === l.id
                ? "bg-accent/20 border border-accent/50 text-accent-light"
                : "bg-card border border-border text-t2 hover:border-border2 hover:text-t1"}`}
          >
            <span>{l.flag}</span>
            {l.name}
          </button>
        ))}
      </div>

      <div className="bg-card border border-border rounded-card p-5 overflow-x-auto mb-9">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <span className="text-xl">{activeLeague.flag}</span>
            <span className="font-heading text-[17px] font-bold text-t1">{activeLeague.name}</span>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-t3 font-body">
            <span className="w-2 h-2 rounded-full bg-accent-light inline-block" /> Top 4
            <span className="w-2 h-2 rounded-full bg-live inline-block ml-2" /> Relegation
          </div>
        </div>
        {activeLeague.sport === "Football" ? (
          <StandingsTable rows={PL_STANDINGS} />
        ) : (
          <div className="text-center py-12 text-t3">
            <span className="text-4xl block mb-3">🔮</span>
            <p className="font-heading text-base font-semibold text-t2 mb-1">Standings loading</p>
            <p className="text-[13px]">IPL standings will populate once the scheduler runs.</p>
          </div>
        )}
      </div>
    </>
  );
}

// ─── Players Tab ──────────────────────────────────────────────────────────────

function PlayersTab() {
  const [sport, setSport] = useState<string>("All");
  const filtered = sport === "All"
    ? TOP_PLAYERS
    : TOP_PLAYERS.filter(p => p.sport === sport);

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
          {filtered.map(p => <PlayerCard key={p.id} player={p} showFollow />)}
        </div>
      ) : (
        <EmptyState message="No players found for this sport." />
      )}
    </>
  );
}

// ─── Events Tab ───────────────────────────────────────────────────────────────

function EventsTab() {
  const [registered, setRegistered] = useState<Set<number>>(new Set());

  return (
    <>
      <SectionHeader title="Fan Events" />
      <div className="flex flex-col gap-4 mb-9">
        {FAN_EVENTS.map((ev: FanEvent) => {
          const isRegistered = registered.has(ev.id);
          const isFull       = ev.registered >= ev.capacity;
          const date         = new Date(ev.eventDate);

          return (
            <div key={ev.id} className="bg-card border border-border rounded-card p-5 hover:border-border2 transition-all duration-200">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-lg">
                      {ev.sport === "Football" ? "⚽" : ev.sport === "Cricket" ? "🏏" : "🥊"}
                    </span>
                    <span className="text-[11px] text-t3 uppercase tracking-widest font-medium">{ev.sport}</span>
                  </div>
                  <h3 className="font-heading text-[17px] font-bold text-t1 mb-1">{ev.title}</h3>
                  <p className="text-[13px] text-t3">{ev.description}</p>
                </div>
                <div className="text-right shrink-0 bg-card2 border border-border rounded-lg px-3 py-2">
                  <div className="font-heading text-[24px] font-bold text-accent-light leading-none">
                    {ev.registered}
                  </div>
                  <div className="text-[11px] text-t3">/ {ev.capacity}</div>
                </div>
              </div>

              <div className="flex items-center gap-5 mb-4 flex-wrap">
                <span className="text-[12px] text-t2">
                  📅 {date.toLocaleDateString("en-GB", { weekday:"short", day:"numeric", month:"short" })}
                  {" · "}
                  {date.toLocaleTimeString("en-GB", { hour:"2-digit", minute:"2-digit" })}
                </span>
                <span className="text-[12px] text-t2">📍 {ev.location}</span>
              </div>

              <CapacityBar registered={ev.registered} capacity={ev.capacity} />

              <button
                onClick={() => { if (!isRegistered && !isFull) setRegistered(prev => new Set([...prev, ev.id])); }}
                disabled={isFull && !isRegistered}
                className={`mt-4 w-full py-2.5 rounded-btn text-sm font-semibold font-heading tracking-wide border-none transition-all duration-200
                  ${isRegistered
                    ? "bg-win/15 text-win cursor-default"
                    : isFull
                      ? "bg-t3/10 text-t3 cursor-not-allowed"
                      : "bg-accent text-white cursor-pointer hover:bg-accent-light hover:shadow-accent-glow"}`}
              >
                {isRegistered ? "✓ Registered!" : isFull ? "Event Full" : "Register Now"}
              </button>
            </div>
          );
        })}
      </div>
    </>
  );
}
