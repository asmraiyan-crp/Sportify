import { SIDEBAR_NAV, PL_STANDINGS } from "../../data";
import { DividerLabel } from "../shared";
import { StandingsTable } from "../standings/StandingsTable";
import type { Page } from "../../types";

// ─── Sidebar ──────────────────────────────────────────────────────────────────

const NAV_TO_PAGE: Record<string, Page> = {
  Home: "home", Football: "matches", Cricket: "matches",
  Wrestling: "matches", Players: "players", Schedule: "matches",
  Events: "events", Trophies: "standings", Analytics: "standings",
};

interface SidebarProps {
  activePage: Page;
  onNav:      (page: Page) => void;
}

export function Sidebar({ activePage, onNav }: SidebarProps) {
  return (
    <aside className="hidden lg:flex flex-col w-[268px] shrink-0 bg-card border-l border-border px-4 py-6 overflow-y-auto">

      <div className="mb-7">
        <DividerLabel label="Quick Nav" />
        <nav className="flex flex-col gap-0.5">
          {SIDEBAR_NAV.map(([icon, label]) => {
            const target = NAV_TO_PAGE[label] ?? "home";
            const active = activePage === target && label !== "Cricket" && label !== "Wrestling";
            return (
              <button
                key={label}
                onClick={() => onNav(target)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer text-[13.5px] font-medium transition-all duration-150 w-full text-left border-none
                  ${active ? "bg-accent/[0.13] text-accent-light" : "text-t2 bg-transparent hover:bg-hover hover:text-t1"}`}
              >
                <span className="text-base w-5 text-center shrink-0">{icon}</span>
                {label}
              </button>
            );
          })}
        </nav>
      </div>

      <div>
        <DividerLabel label="Premier League" />
        <StandingsTable rows={PL_STANDINGS} compact />
      </div>
    </aside>
  );
}

// ─── Footer ───────────────────────────────────────────────────────────────────

const FOOTER_LINKS = ["About", "Privacy", "API Docs", "GitHub"] as const;

export function Footer() {
  return (
    <footer className="border-t border-border px-7 py-5 flex items-center justify-between bg-base flex-wrap gap-3 shrink-0">
      <span className="font-display text-[20px] tracking-widest text-t3">⚡ SPORTIFY</span>
      <span className="text-[12px] text-t3">© 2025 Sportify · DBMS Course · Team Raiyan</span>
      <div className="flex gap-4">
        {FOOTER_LINKS.map(l => (
          <a key={l} className="text-[12px] text-t3 cursor-pointer hover:text-accent-light transition-colors duration-150 no-underline">
            {l}
          </a>
        ))}
      </div>
    </footer>
  );
}
