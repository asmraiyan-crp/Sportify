import { LANDING_STATS, LANDING_FEATURES, HERO_GRADIENTS } from "../data";

interface LandingPageProps {
  onGetStarted: () => void;
}

interface LandingStat    { value: string; label: string }
interface LandingFeature { icon: string; title: string; desc: string }

export function LandingPage({ onGetStarted }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-base text-t1 font-body overflow-x-hidden">

      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        <div className="absolute inset-0" style={{ background: HERO_GRADIENTS["football-pl"] }} />
        <div className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, #3ecf8e 0%, transparent 70%)", transform: "translate(30%, -30%)" }} />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full opacity-10"
          style={{ background: "radial-gradient(circle, #7c3aed 0%, transparent 70%)", transform: "translate(-30%, 30%)" }} />
        <div className="absolute inset-0 opacity-[0.04]"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")" }} />
        <div className="absolute bottom-0 inset-x-0 h-40 bg-gradient-to-t from-base to-transparent" />

        <div className="relative z-10 max-w-6xl mx-auto px-8 py-24 grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-live/10 border border-live/30 text-live text-xs font-bold tracking-widest mb-8 font-heading">
              <span className="w-1.5 h-1.5 rounded-full bg-live animate-pulse2" />
              LIVE SCORES UPDATED EVERY 60s
            </div>

            <h1 className="font-display text-[72px] leading-none text-white tracking-tight mb-6">
              YOUR SPORTS.
              <br />
              <span className="text-transparent" style={{ WebkitTextStroke: "1px rgba(255,255,255,0.3)" }}>
                ALL OF THEM.
              </span>
            </h1>

            <p className="text-[17px] text-white/60 leading-relaxed mb-10 font-body max-w-md">
              Football, Cricket, Wrestling — live scores, deep statistics, standings, and a fan community.
              One platform. Real data. Zero lag.
            </p>

            <div className="flex gap-3 flex-wrap">
              <button
                onClick={onGetStarted}
                className="flex items-center gap-2 px-7 py-3.5 rounded-btn text-base font-bold bg-accent text-white border-none cursor-pointer font-heading tracking-wide transition-all duration-200 hover:bg-accent-light hover:shadow-accent-glow hover:-translate-y-0.5 active:translate-y-0"
              >
                Get Started Free →
              </button>
              <button className="px-7 py-3.5 rounded-btn text-base font-bold bg-white/[0.06] text-white border border-white/15 cursor-pointer font-heading tracking-wide transition-all duration-200 hover:bg-white/[0.12]">
                Watch Demo
              </button>
            </div>
          </div>

          <div className="hidden lg:flex justify-end">
            <LiveScorePreview />
          </div>
        </div>
      </section>

      {/* ── STATS BAR ─────────────────────────────────────────────────────── */}
      <section className="bg-card border-y border-border py-10">
        <div className="max-w-4xl mx-auto px-8 grid grid-cols-2 md:grid-cols-4 gap-8">
          {LANDING_STATS.map((s: LandingStat) => (
            <div key={s.label} className="text-center">
              <div className="font-display text-[42px] text-accent-light leading-none mb-1">{s.value}</div>
              <div className="text-[13px] text-t3 font-body">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ──────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-8 py-24">
        <div className="text-center mb-16">
          <p className="text-[11px] font-bold tracking-[0.2em] text-accent-light uppercase font-heading mb-3">
            What You Get
          </p>
          <h2 className="font-display text-[48px] text-white leading-none">
            BUILT FOR FANS.<br />
            <span className="text-t3">POWERED BY DATA.</span>
          </h2>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {LANDING_FEATURES.map((f: LandingFeature, i: number) => (
            <div
              key={f.title}
              className="group bg-card border border-border rounded-card p-6 hover:border-accent/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-accent-glow-lg"
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              <div className="w-11 h-11 rounded-lg bg-accent/10 flex items-center justify-center text-xl mb-4 group-hover:bg-accent/20 transition-colors duration-200">
                {f.icon}
              </div>
              <h3 className="font-heading text-[17px] font-bold text-t1 mb-2">{f.title}</h3>
              <p className="text-[13.5px] text-t3 leading-relaxed font-body">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── SPORTS SHOWCASE ───────────────────────────────────────────────── */}
      <section className="bg-card border-y border-border py-24">
        <div className="max-w-6xl mx-auto px-8">
          <div className="text-center mb-14">
            <h2 className="font-display text-[48px] text-white leading-none mb-3">THREE SPORTS. ONE HOME.</h2>
            <p className="text-t3 font-body text-[15px]">Deep coverage across Football, Cricket, and Wrestling.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-5">
            {[
              { sport: "Football",  icon: "⚽", bg: HERO_GRADIENTS["football-pl"],    stat: "8,400+ matches",  tagline: "Premier League, UCL, La Liga & more" },
              { sport: "Cricket",   icon: "🏏", bg: HERO_GRADIENTS["cricket-ipl"],    stat: "2,100+ matches",  tagline: "IPL, BBL, international T20 & ODI"   },
              { sport: "Wrestling", icon: "🥊", bg: HERO_GRADIENTS["wrestling-wwe"],  stat: "1,800+ events",   tagline: "WWE Raw, SmackDown, WrestleMania"     },
            ].map(s => (
              <div
                key={s.sport}
                className="relative rounded-card overflow-hidden h-[220px] flex flex-col justify-end p-6 cursor-pointer group"
                style={{ background: s.bg }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                <div className="absolute inset-0 bg-card-glow opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative z-10">
                  <div className="text-4xl mb-2">{s.icon}</div>
                  <div className="font-display text-[28px] text-white leading-none">{s.sport.toUpperCase()}</div>
                  <div className="text-[12px] text-white/50 mt-1 font-body">{s.tagline}</div>
                  <div className="font-heading text-[13px] font-bold text-accent-light mt-2">{s.stat}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-8 py-28 text-center">
        <h2 className="font-display text-[60px] text-white leading-none mb-6">READY TO PLAY?</h2>
        <p className="text-[17px] text-t3 mb-10 font-body max-w-lg mx-auto">
          Join thousands of fans already tracking live scores, following teams, and building their sports community.
        </p>
        <button
          onClick={onGetStarted}
          className="inline-flex items-center gap-3 px-9 py-4 rounded-btn text-lg font-bold bg-accent text-white border-none cursor-pointer font-heading tracking-wide transition-all duration-200 hover:bg-accent-light hover:shadow-accent-glow hover:-translate-y-0.5"
        >
          ⚡ Join Sportify Free
        </button>
      </section>

      {/* ── FOOTER ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-border px-8 py-6 flex items-center justify-between flex-wrap gap-3 text-[12px] text-t3">
        <span className="font-display text-[20px] tracking-widest">⚡ SPORTIFY</span>
        <span>© 2025 Sportify · DBMS Course · Team Raiyan</span>
        <div className="flex gap-5">
          {["About","Privacy","GitHub"].map(l => (
            <a key={l} className="hover:text-accent-light cursor-pointer transition-colors">{l}</a>
          ))}
        </div>
      </footer>
    </div>
  );
}

// ─── Live Score Preview (decorative) ─────────────────────────────────────────

function LiveScorePreview() {
  return (
    <div className="w-[340px] space-y-3">
      <div className="bg-card/80 backdrop-blur-md border border-border2 rounded-card p-5 shadow-accent-glow">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[11px] text-t3 uppercase tracking-widest font-medium">Premier League</span>
          <span className="text-[10px] font-bold text-live bg-live/10 border border-live/30 px-2 py-0.5 rounded font-heading">
            ● LIVE
          </span>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-center flex-1">
            <div className="text-3xl mb-2">⚽</div>
            <div className="font-heading font-bold text-t1 text-sm">Arsenal</div>
          </div>
          <div className="text-center px-4">
            <div className="font-display text-[36px] text-t1 tracking-wide">2 : 1</div>
            <div className="text-[11px] text-live font-semibold mt-1">67'</div>
          </div>
          <div className="text-center flex-1">
            <div className="text-3xl mb-2">⚽</div>
            <div className="font-heading font-bold text-t1 text-sm">Chelsea</div>
          </div>
        </div>
      </div>

      {[
        { home: "MI 🏏", away: "CSK 🏏", league: "IPL 2025",  time: "19:30", sport: "Cricket"  },
        { home: "Bayern ⚽", away: "PSG ⚽", league: "UCL",    time: "21:00", sport: "Football" },
      ].map(m => (
        <div key={m.league} className="bg-card/60 backdrop-blur-md border border-border rounded-lg px-4 py-3 flex items-center gap-3">
          <div className="text-xl shrink-0">{m.sport === "Cricket" ? "🏏" : "⚽"}</div>
          <div className="flex-1 min-w-0">
            <div className="font-heading text-sm font-bold text-t1 truncate">{m.home} vs {m.away}</div>
            <div className="text-[11px] text-t3">{m.league}</div>
          </div>
          <div className="font-heading font-bold text-accent-light text-sm">{m.time}</div>
        </div>
      ))}
    </div>
  );
}
