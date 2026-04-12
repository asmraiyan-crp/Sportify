// ─── Enums ────────────────────────────────────────────────────────────────────

export type Sport        = "Football" | "Cricket" | "Wrestling";
export type SportFilter  = "All" | Sport;
export type MatchStatus  = "live" | "soon" | "finished" | "scheduled";
export type HeroTag      = "LIVE" | "TRENDING" | "WATCH";
export type FormResult   = "W" | "D" | "L";
export type UserRole     = "fan" | "team_manager" | "admin";
export type InjuryStatus = "fit" | "injured" | "doubtful";

// ─── Core Entities ────────────────────────────────────────────────────────────

export interface Team {
  id:           number;
  name:         string;
  badge:        string;
  country?:     string;
  sport:        Sport;
  logoUrl?:     string;
  foundedYear?: number;
  homeGround?:  string;
}

export interface Player {
  id:           number;
  name:         string;
  team:         string;
  teamId:       number;
  sport:        Sport;
  position:     string;
  rating:       number;
  injuryStatus: InjuryStatus;
  img:          string;
  nationality?: string;
  stats:        PlayerStats;
}

export interface PlayerStats {
  goals?:   number;
  assists?: number;
  runs?:    number;
  wickets?: number;
  matches?: number;
}

export interface Match {
  id:          number;
  sport:       Sport;
  league:      string;
  leagueId:    number;
  home:        Team;
  away:        Team;
  homeScore:   number | string | null;
  awayScore:   number | string | null;
  elapsed:     string | null;
  status:      MatchStatus;
  venue?:      string;
  datetime?:   string;
}

export interface Standing {
  pos:    number;
  team:   string;
  badge:  string;
  played: number;
  won:    number;
  drawn:  number;
  lost:   number;
  gf:     number;
  ga:     number;
  pts:    number;
  form:   FormResult[];
}

export interface FanEvent {
  id:          number;
  title:       string;
  description: string;
  eventDate:   string;
  location:    string;
  capacity:    number;
  registered:  number;
  sport:       Sport;
}

export interface HeroSlide {
  id:     number;
  title:  string;
  league: string;
  tag:    HeroTag;
  bgKey:  string;
  score:  string | null;
  time:   string;
  sport:  Sport;
}

// ─── Auth / User ──────────────────────────────────────────────────────────────

export interface AuthUser {
  id:          string;
  displayName: string;
  email:       string;
  role:        UserRole;
  avatarInitial: string;
  teamManaged: number | null;
  joinedAt:    string;
  followedTeams:   Team[];
  followedPlayers: Player[];
}

// ─── API Shapes (what your Flask backend returns) ─────────────────────────────

export interface ApiResponse<T> {
  data:    T;
  message?: string;
}

export interface PaginatedResponse<T> {
  data:    T[];
  total:   number;
  page:    number;
  limit:   number;
}

// ─── UI State ─────────────────────────────────────────────────────────────────

export type Page = "home" | "matches" | "standings" | "players" | "events" | "profile" | "landing"| "signup";