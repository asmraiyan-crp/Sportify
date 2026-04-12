import { useState } from "react";
import type { AuthUser, Team, Player } from "../types";
import { TOP_PLAYERS } from "../data";
import { PlayerCard }  from "../components/player/PlayerCard";
import { StatPill, SectionHeader, DividerLabel } from "../components/shared";

interface ProfilePageProps {
  user:   AuthUser;
  onBack: () => void;
}

type ProfileTab = "overview" | "following" | "activity" | "settings";

export function ProfilePage({ user, onBack }: ProfilePageProps) {
  const [activeTab, setActiveTab] = useState<ProfileTab>("overview");

  return (
    <div className="max-w-4xl mx-auto">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-t3 hover:text-t1 transition-colors text-[13px] font-body mb-6 bg-transparent border-none cursor-pointer"
      >
        ← Back to Dashboard
      </button>

      <ProfileHeader user={user} />

      <div className="flex gap-0 mt-6 border-b border-border">
        {(["overview","following","activity","settings"] as ProfileTab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-3 text-[13px] font-medium font-body capitalize transition-all duration-150 border-none cursor-pointer border-b-2 -mb-px
              ${activeTab === tab
                ? "text-t1 border-accent bg-transparent"
                : "text-t3 border-transparent bg-transparent hover:text-t2"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {activeTab === "overview"  && <OverviewTab  user={user} />}
        {activeTab === "following" && <FollowingTab user={user} />}
        {activeTab === "activity"  && <ActivityTab />}
        {activeTab === "settings"  && <SettingsTab  user={user} />}
      </div>
    </div>
  );
}

// ─── Profile Header ───────────────────────────────────────────────────────────

function ProfileHeader({ user }: { user: AuthUser }) {
  const roleColors: Record<string, string> = {
    fan:          "bg-accent/20 text-accent-light border-accent/40",
    team_manager: "bg-[#f59e0b]/15 text-[#f59e0b] border-[#f59e0b]/30",
    admin:        "bg-live/15 text-live border-live/30",
  };
  const roleLabel: Record<string, string> = {
    fan: "Sports Fan", team_manager: "Team Manager", admin: "Admin",
  };
  const joinDate = new Date(user.joinedAt).toLocaleDateString("en-GB", {
    month: "long", year: "numeric",
  });

  return (
    <div className="bg-card border border-border rounded-card overflow-hidden">
      <div className="h-24 bg-gradient-to-r from-accent/30 via-purple-900/20 to-transparent relative">
        <div className="absolute inset-0 opacity-10"
          style={{ backgroundImage: "repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.02) 10px, rgba(255,255,255,0.02) 20px)" }} />
      </div>

      <div className="px-6 pb-6 -mt-8">
        <div className="flex items-end justify-between mb-4">
          <div className="w-16 h-16 rounded-xl bg-accent/30 border-4 border-card flex items-center justify-center font-display text-[28px] text-accent-light shadow-accent-glow">
            {user.avatarInitial}
          </div>
          <button className="flex items-center gap-1.5 px-4 py-1.5 rounded-btn text-[12px] font-semibold text-t2 border border-border bg-transparent hover:border-accent hover:text-t1 transition-all cursor-pointer font-heading tracking-wide">
            ✏️ Edit Profile
          </button>
        </div>

        <div className="flex items-center gap-3 mb-1">
          <h1 className="font-heading text-[22px] font-bold text-t1">{user.displayName}</h1>
          <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border font-heading tracking-wide ${roleColors[user.role]}`}>
            {roleLabel[user.role]}
          </span>
        </div>
        <p className="text-[13px] text-t3 font-body mb-5">{user.email} · Member since {joinDate}</p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatPill value={user.followedTeams.length}   label="Teams Followed"   />
          <StatPill value={user.followedPlayers.length} label="Players Followed" />
          <StatPill value={24}                          label="Reviews Posted"   />
          <StatPill value={3}                           label="Events Attended"  accent />
        </div>
      </div>
    </div>
  );
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab({ user }: { user: AuthUser }) {
  return (
    <div className="space-y-8">
      <div>
        <SectionHeader title="My Teams" linkText="Manage" />
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {user.followedTeams.map((team: Team) => (
            <div key={team.id} className="bg-card border border-border rounded-card p-4 text-center hover:border-accent transition-all duration-200 cursor-pointer group">
              <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">{team.badge}</div>
              <div className="font-heading text-sm font-bold text-t1">{team.name}</div>
              <div className="text-[11px] text-t3 mt-0.5">{team.country}</div>
            </div>
          ))}
          <div className="bg-card border border-dashed border-border2 rounded-card p-4 text-center hover:border-accent transition-all duration-200 cursor-pointer flex flex-col items-center justify-center gap-1">
            <span className="text-2xl text-t3">+</span>
            <span className="text-[12px] text-t3 font-body">Follow a Team</span>
          </div>
        </div>
      </div>

      <div>
        <SectionHeader title="My Players" linkText="Manage" />
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {user.followedPlayers.map((p: Player) => (
            <PlayerCard key={p.id} player={p} showFollow isFollowed />
          ))}
          <div className="bg-card border border-dashed border-border2 rounded-card p-4 text-center hover:border-accent transition-all duration-200 cursor-pointer flex flex-col items-center justify-center gap-1">
            <span className="text-2xl text-t3">+</span>
            <span className="text-[12px] text-t3 font-body">Follow a Player</span>
          </div>
        </div>
      </div>

      <div>
        <SectionHeader title="Recent Reviews" />
        <div className="space-y-3">
          {[
            { match: "Arsenal vs Chelsea",  rating: 5, text: "What a game! Saka's late winner was electric.",    date: "2 days ago"  },
            { match: "MI vs CSK IPL",       rating: 4, text: "Brilliant batting from Rohit. Thriller finish.",   date: "5 days ago"  },
            { match: "WrestleMania Main",   rating: 5, text: "Cody's championship reign continues impressively.",date: "1 week ago"   },
          ].map((r, i) => (
            <div key={i} className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-heading text-sm font-bold text-t1">{r.match}</span>
                <div className="flex items-center gap-1">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <span key={j} className={`text-[12px] ${j < r.rating ? "text-soon" : "text-border2"}`}>★</span>
                  ))}
                </div>
              </div>
              <p className="text-[13px] text-t3 font-body">{r.text}</p>
              <span className="text-[11px] text-t3/60 mt-1 block">{r.date}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Following Tab ────────────────────────────────────────────────────────────

function FollowingTab({ user }: { user: AuthUser }) {
  return (
    <div className="space-y-8">
      <div>
        <DividerLabel label={`Teams (${user.followedTeams.length})`} />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {user.followedTeams.map((team: Team) => (
            <div key={team.id} className="group bg-card border border-border rounded-card p-4 flex flex-col items-center gap-2 hover:border-live transition-all duration-200 cursor-pointer">
              <div className="text-4xl group-hover:scale-110 transition-transform">{team.badge}</div>
              <div className="font-heading text-sm font-bold text-t1">{team.name}</div>
              <div className="text-[11px] text-t3">{team.sport} · {team.country}</div>
              <button className="text-[11px] text-live/70 hover:text-live font-semibold font-heading border-none bg-transparent cursor-pointer">
                Unfollow
              </button>
            </div>
          ))}
        </div>
      </div>

      <div>
        <DividerLabel label={`Players (${user.followedPlayers.length})`} />
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {user.followedPlayers.map((p: Player) => (
            <PlayerCard key={p.id} player={p} showFollow isFollowed />
          ))}
        </div>
      </div>

      <div>
        <DividerLabel label="Discover Players" />
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {TOP_PLAYERS
            .filter((p: Player) => !user.followedPlayers.find((fp: Player) => fp.id === p.id))
            .map((p: Player) => <PlayerCard key={p.id} player={p} showFollow />)
          }
        </div>
      </div>
    </div>
  );
}

// ─── Activity Tab ─────────────────────────────────────────────────────────────

const ACTIVITY = [
  { icon: "⭐", text: "Reviewed Arsenal vs Chelsea",          sub: "5 stars · 2 days ago"  },
  { icon: "➕", text: "Started following Bukayo Saka",         sub: "4 days ago"            },
  { icon: "⭐", text: "Reviewed MI vs CSK IPL",                sub: "4 stars · 5 days ago"  },
  { icon: "🎪", text: "Registered for UCL Watch Party",        sub: "1 week ago"            },
  { icon: "➕", text: "Started following Arsenal",             sub: "2 weeks ago"           },
  { icon: "💬", text: "Commented on WrestleMania Main Event",  sub: "2 weeks ago"           },
  { icon: "➕", text: "Started following Mumbai Indians",      sub: "3 weeks ago"           },
  { icon: "⭐", text: "Reviewed WrestleMania Main Event",      sub: "5 stars · 3 weeks ago" },
];

function ActivityTab() {
  return (
    <div>
      <SectionHeader title="Activity Feed" />
      <div className="relative">
        <div className="absolute left-5 top-2 bottom-2 w-px bg-border" />
        <div className="space-y-1">
          {ACTIVITY.map((a, i) => (
            <div key={i} className="flex items-start gap-4 pl-3 py-3 hover:bg-hover/30 rounded-lg transition-colors duration-100 cursor-default">
              <div className="relative z-10 w-5 h-5 rounded-full bg-card2 border border-border2 flex items-center justify-center text-[11px] shrink-0 mt-0.5">
                {a.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-body text-[14px] text-t1">{a.text}</div>
                <div className="text-[12px] text-t3 mt-0.5">{a.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Settings Tab ─────────────────────────────────────────────────────────────

function SettingsTab({ user }: { user: AuthUser }) {
  const [displayName, setDisplayName] = useState(user.displayName);
  const [notifs, setNotifs] = useState({
    liveAlerts:       true,
    weeklyDigest:     false,
    eventReminders:   true,
    communityReplies: true,
  });

  const notifLabels: Record<string, string> = {
    liveAlerts:       "Live match alerts for followed teams",
    weeklyDigest:     "Weekly stats digest email",
    eventReminders:   "Fan event reminders",
    communityReplies: "Replies to your comments",
  };

  return (
    <div className="space-y-6 max-w-lg">
      {/* Account */}
      <div className="bg-card border border-border rounded-card p-5">
        <h3 className="font-heading text-[15px] font-bold text-t1 mb-4">Account Details</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-[12px] text-t3 font-body mb-1.5 uppercase tracking-wide">Display Name</label>
            <input
              value={displayName}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDisplayName(e.target.value)}
              className="w-full bg-card2 border border-border2 rounded-lg px-3 py-2 text-[14px] text-t1 font-body outline-none focus:border-accent transition-colors"
            />
          </div>
          <div>
            <label className="block text-[12px] text-t3 font-body mb-1.5 uppercase tracking-wide">Email</label>
            <input
              value={user.email}
              disabled
              className="w-full bg-card2/50 border border-border rounded-lg px-3 py-2 text-[14px] text-t3 font-body cursor-not-allowed"
            />
            <p className="text-[11px] text-t3 mt-1">Email changes require verification via backend.</p>
          </div>
          <div>
            <label className="block text-[12px] text-t3 font-body mb-1.5 uppercase tracking-wide">Role</label>
            <div className="flex items-center gap-2 px-3 py-2 bg-card2/50 border border-border rounded-lg">
              <span className="text-[14px] text-t2 font-body capitalize">{user.role.replace("_"," ")}</span>
              <span className="text-[11px] text-t3">· Contact admin to change role</span>
            </div>
          </div>
          <button className="px-5 py-2 rounded-btn text-[13px] font-semibold bg-accent text-white border-none cursor-pointer font-heading hover:bg-accent-light transition-all">
            Save Changes
          </button>
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-card border border-border rounded-card p-5">
        <h3 className="font-heading text-[15px] font-bold text-t1 mb-4">Notifications</h3>
        <div className="space-y-3">
          {(Object.keys(notifs) as Array<keyof typeof notifs>).map(key => (
            <div key={key} className="flex items-center justify-between py-2 border-b border-border last:border-0">
              <span className="text-[13.5px] text-t2 font-body">{notifLabels[key]}</span>
              <button
                onClick={() => setNotifs(n => ({ ...n, [key]: !n[key] }))}
                className={`relative w-10 rounded-full transition-colors duration-200 border-none cursor-pointer flex-shrink-0 ${notifs[key] ? "bg-accent" : "bg-border2"}`}
                style={{ height: "22px" }}
              >
                <span
                  className={`absolute top-[3px] w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${notifs[key] ? "translate-x-5" : "translate-x-[3px]"}`}
                  style={{ left: 0 }}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Danger zone */}
      <div className="bg-live/5 border border-live/20 rounded-card p-5">
        <h3 className="font-heading text-[15px] font-bold text-live mb-3">Danger Zone</h3>
        <p className="text-[13px] text-t3 mb-4 font-body">These actions are irreversible. Proceed with caution.</p>
        <div className="flex gap-3">
          <button className="px-4 py-2 rounded-btn text-[12px] font-semibold text-t2 border border-border bg-transparent hover:border-live hover:text-live transition-all cursor-pointer font-heading">
            Deactivate Account
          </button>
          <button className="px-4 py-2 rounded-btn text-[12px] font-semibold text-live/80 border border-live/30 bg-live/10 hover:bg-live/20 transition-all cursor-pointer font-heading">
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
}
