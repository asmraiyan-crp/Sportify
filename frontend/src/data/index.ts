import type {
  Match, Player, Standing, HeroSlide, FanEvent,
  AuthUser, SportFilter, Team,
} from "../types";

// ─── Sport metadata ───────────────────────────────────────────────────────────

export const SPORT_FILTERS: SportFilter[] = ["All", "Football", "Cricket", "Wrestling"];

export const SPORT_ICON: Record<string, string> = {
  Football:  "⚽",
  Cricket:   "🏏",
  Wrestling: "🥊",
  All:       "🌐",
};

export const SPORT_COLOR: Record<string, string> = {
  Football:  "#3ecf8e",
  Cricket:   "#f59e0b",
  Wrestling: "#ef4444",
};

// ─── Hero gradient map (runtime — can't be JIT Tailwind) ──────────────────────

export const HERO_GRADIENTS: Record<string, string> = {
  "football-pl":   "linear-gradient(135deg,#1a0a2e 0%,#2d1060 50%,#0f0a1e 100%)",
  "football-ucl":  "linear-gradient(135deg,#0a1628 0%,#1e3a5f 50%,#0a0f1e 100%)",
  "cricket-ipl":   "linear-gradient(135deg,#1a0e00 0%,#4d2e00 50%,#1a0a00 100%)",
  "wrestling-wwe": "linear-gradient(135deg,#1e0a0a 0%,#4d1010 50%,#150505 100%)",
  "football-laliga":"linear-gradient(135deg,#001a0a 0%,#003d20 50%,#001008 100%)",
};

// ─── Hero Slides ──────────────────────────────────────────────────────────────

export const HERO_SLIDES: HeroSlide[] = [
  {
    id: 1, tag: "LIVE", sport: "Football",
    title: "Arsenal vs Chelsea", league: "Premier League · Match Day 28",
    bgKey: "football-pl", score: "2 – 1", time: "67'",
  },
  {
    id: 2, tag: "TRENDING", sport: "Football",
    title: "Champions League Semi Final",
    league: "UCL 2024–25 · Real Madrid vs Bayern",
    bgKey: "football-ucl", score: null, time: "Tomorrow · 21:00",
  },
  {
    id: 3, tag: "LIVE", sport: "Cricket",
    title: "MI vs CSK IPL Thriller",
    league: "IPL 2025 · Match 42",
    bgKey: "cricket-ipl", score: "187 – 162/7", time: "18.4 ov",
  },
  {
    id: 4, tag: "WATCH", sport: "Wrestling",
    title: "WrestleMania 41 Highlights",
    league: "WWE · Main Event Recap",
    bgKey: "wrestling-wwe", score: null, time: "3h 47m",
  },
];

// ─── Teams ────────────────────────────────────────────────────────────────────

const ARSENAL:      Team = { id: 1,  name: "Arsenal",     badge: "⚽", sport: "Football", country: "England" };
const CHELSEA:      Team = { id: 2,  name: "Chelsea",     badge: "⚽", sport: "Football", country: "England" };
const REAL_MADRID:  Team = { id: 3,  name: "Real Madrid", badge: "⚽", sport: "Football", country: "Spain"   };
const BARCELONA:    Team = { id: 4,  name: "Barcelona",   badge: "⚽", sport: "Football", country: "Spain"   };
const MAN_CITY:     Team = { id: 5,  name: "Man City",    badge: "⚽", sport: "Football", country: "England" };
const LIVERPOOL:    Team = { id: 6,  name: "Liverpool",   badge: "⚽", sport: "Football", country: "England" };
const MI:           Team = { id: 7,  name: "MI",          badge: "🏏", sport: "Cricket",  country: "India"   };
const CSK:          Team = { id: 8,  name: "CSK",         badge: "🏏", sport: "Cricket",  country: "India"   };
const CODY_RHODES:  Team = { id: 9,  name: "Cody Rhodes", badge: "🥊", sport: "Wrestling",country: "USA"     };
const SETH_ROLLINS: Team = { id: 10, name: "Seth Rollins",badge: "🥊", sport: "Wrestling",country: "USA"     };
const RCB:          Team = { id: 11, name: "RCB",         badge: "🏏", sport: "Cricket",  country: "India"   };
const KKR:          Team = { id: 12, name: "KKR",         badge: "🏏", sport: "Cricket",  country: "India"   };
const BAYERN:       Team = { id: 13, name: "Bayern",      badge: "⚽", sport: "Football", country: "Germany" };
const PSG:          Team = { id: 14, name: "PSG",         badge: "⚽", sport: "Football", country: "France"  };

// ─── Live Matches ─────────────────────────────────────────────────────────────

export const LIVE_MATCHES: Match[] = [
  { id: 1,  sport: "Football",  league: "Premier League", leagueId: 1, home: ARSENAL,     away: CHELSEA,      homeScore: 2,   awayScore: 1,       elapsed: "67'",     status: "live"      },
  { id: 2,  sport: "Cricket",   league: "IPL 2025",       leagueId: 4, home: MI,          away: CSK,          homeScore: 187, awayScore: "162/7", elapsed: "18.4 ov", status: "live"      },
  { id: 3,  sport: "Football",  league: "La Liga",        leagueId: 2, home: REAL_MADRID, away: BARCELONA,    homeScore: 1,   awayScore: 1,       elapsed: "45'",     status: "live"      },
  { id: 4,  sport: "Wrestling", league: "WWE Raw",        leagueId: 5, home: CODY_RHODES, away: SETH_ROLLINS, homeScore: null,awayScore: null,    elapsed: null,      status: "soon"      },
];

export const UPCOMING_MATCHES: Match[] = [
  { id: 11, sport: "Football", league: "Premier League", leagueId: 1, home: MAN_CITY, away: LIVERPOOL, homeScore: null, awayScore: null, elapsed: null, status: "scheduled", datetime: "Sun 2 Mar · 16:30" },
  { id: 12, sport: "Cricket",  league: "IPL 2025",       leagueId: 4, home: RCB,      away: KKR,       homeScore: null, awayScore: null, elapsed: null, status: "scheduled", datetime: "Mon 3 Mar · 19:30" },
  { id: 13, sport: "Football", league: "UCL",            leagueId: 3, home: BAYERN,   away: PSG,       homeScore: null, awayScore: null, elapsed: null, status: "scheduled", datetime: "Tue 4 Mar · 20:00" },
];

// ─── Standings ────────────────────────────────────────────────────────────────

export const PL_STANDINGS: Standing[] = [
  { pos:1, team:"Arsenal",   badge:"⚽", played:27, won:18, drawn:6, lost:3, gf:56, ga:24, pts:60, form:["W","W","W","D","W"] },
  { pos:2, team:"Liverpool", badge:"⚽", played:27, won:17, drawn:6, lost:4, gf:52, ga:28, pts:57, form:["W","D","W","W","L"] },
  { pos:3, team:"Man City",  badge:"⚽", played:27, won:16, drawn:5, lost:6, gf:49, ga:31, pts:53, form:["L","W","W","W","D"] },
  { pos:4, team:"Chelsea",   badge:"⚽", played:27, won:14, drawn:7, lost:6, gf:44, ga:33, pts:49, form:["W","D","L","W","W"] },
  { pos:5, team:"Tottenham", badge:"⚽", played:27, won:12, drawn:8, lost:7, gf:40, ga:37, pts:44, form:["D","W","D","L","W"] },
  { pos:6, team:"Newcastle", badge:"⚽", played:27, won:12, drawn:6, lost:9, gf:38, ga:39, pts:42, form:["L","L","W","W","D"] },
];

// ─── Players ──────────────────────────────────────────────────────────────────

export const TOP_PLAYERS: Player[] = [
  { id:1, name:"Bukayo Saka",    team:"Arsenal",        teamId:1, sport:"Football",  position:"Winger",     rating:9.1, injuryStatus:"fit",      img:"🏃", stats:{ goals:18, assists:14, matches:27 } },
  { id:2, name:"Erling Haaland", team:"Man City",       teamId:5, sport:"Football",  position:"Striker",    rating:9.4, injuryStatus:"fit",      img:"⚡", stats:{ goals:27, assists:5,  matches:25 } },
  { id:3, name:"Rohit Sharma",   team:"Mumbai Indians", teamId:7, sport:"Cricket",   position:"Batsman",    rating:8.8, injuryStatus:"fit",      img:"🏏", stats:{ runs:1024, matches:14 } },
  { id:4, name:"Virat Kohli",    team:"RCB",            teamId:11,sport:"Cricket",   position:"Batsman",    rating:9.2, injuryStatus:"fit",      img:"🏆", stats:{ runs:892, matches:13 } },
  { id:5, name:"Cody Rhodes",    team:"WWE",            teamId:9, sport:"Wrestling", position:"Wrestler",   rating:8.9, injuryStatus:"fit",      img:"💪", stats:{ matches:22 } },
  { id:6, name:"Pedri",          team:"Barcelona",      teamId:4, sport:"Football",  position:"Midfielder", rating:8.7, injuryStatus:"doubtful", img:"🎯", stats:{ goals:9, assists:11, matches:24 } },
];

// ─── Fan Events ───────────────────────────────────────────────────────────────

export const FAN_EVENTS: FanEvent[] = [
  { id:1, title:"UCL Semi-Final Watch Party",      description:"Live screening with commentary, giveaways & food.",       eventDate:"2025-04-09T19:00:00Z", location:"Dhaka Sports Hub",   capacity:200, registered:143, sport:"Football"  },
  { id:2, title:"Cricket Analytics Workshop",      description:"Data-driven IPL 2025 breakdown with senior analysts.",    eventDate:"2025-04-15T15:00:00Z", location:"Online (Zoom)",      capacity:100, registered:67,  sport:"Cricket"   },
  { id:3, title:"WWE WrestleMania Viewing Night",  description:"Watch the main event live with fellow wrestling fans.",   eventDate:"2025-04-06T22:00:00Z", location:"The Ring Bar, Dhaka", capacity:80,  registered:72,  sport:"Wrestling" },
];

// ─── Mock Auth User ───────────────────────────────────────────────────────────

export const MOCK_USER: AuthUser = {
  id:            "usr_raiyan_001",
  displayName:   "A S M Raiyan",
  email:         "raiyan@sportify.dev",
  role:          "fan",
  avatarInitial: "R",
  teamManaged:   null,
  joinedAt:      "2025-01-15T00:00:00Z",
  followedTeams:   [ARSENAL, MI],
  followedPlayers: [TOP_PLAYERS[0], TOP_PLAYERS[2]],
};

// ─── Nav ──────────────────────────────────────────────────────────────────────

export const NAV_LINKS = ["Home", "Matches", "Standings", "Players", "Events"] as const;
export type  NavLink = (typeof NAV_LINKS)[number];

export const SIDEBAR_NAV: [string, string][] = [
  ["🏠","Home"], ["⚽","Football"], ["🏏","Cricket"],
  ["🥊","Wrestling"], ["📊","Analytics"], ["🎯","Players"],
  ["🏆","Trophies"], ["📅","Schedule"], ["🎪","Events"],
];

// ─── Landing Page stats (marketing numbers) ──────────────────────────────────

export const LANDING_STATS = [
  { value: "12K+",  label: "Live Matches Tracked" },
  { value: "3",     label: "Sports Covered"       },
  { value: "50K+",  label: "Fans Registered"      },
  { value: "60s",   label: "Score Refresh Rate"   },
];

export const LANDING_FEATURES = [
  { icon: "⚡", title: "Real-Time Scores",     desc: "Live scores pushed every 60 seconds directly from official APIs. Never miss a goal, wicket, or pin."   },
  { icon: "📊", title: "Deep Statistics",      desc: "Per-player stats, match history, season aggregates, and standings updated automatically after every match." },
  { icon: "👥", title: "Fan Community",        desc: "Rate matches, post reviews, follow your favourite teams and players, join fan events."                     },
  { icon: "🏆", title: "Multi-Sport",          desc: "Football, Cricket, and Wrestling under one roof. One account, three sports, zero friction."                },
  { icon: "🔔", title: "Smart Notifications",  desc: "Get notified the instant a team you follow goes live. Never accidentally miss kickoff again."              },
  { icon: "🛡", title: "Role-Based Access",    desc: "Team Managers update squads and injury status. Admins moderate content. Fans explore everything."          },
];
