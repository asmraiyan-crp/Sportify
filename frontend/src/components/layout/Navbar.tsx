import { useNavigate } from "react-router-dom";
import type { AuthUser } from "../../types";

interface NavbarProps {
  activePage:    string;
  setActivePage: (p: string) => void;
  searchQ:       string;
  setSearchQ:    (q: string) => void;
  user:          AuthUser | null;
  onLogin:       () => void;
  onProfile:     () => void;
  onSignOut:     () => void;
  onSignup:      () => void;
}

export function Navbar({ searchQ, setSearchQ, user, onSignOut }: NavbarProps) {
  const navigate = useNavigate();

  const handleSignOut = () => {
    onSignOut();
    navigate("/landing");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  const handleLogoClick = () => {
    if (user) {
      navigate("/home");
    } else {
      navigate("/landing");
    }
  };

  return (
    <nav className="sticky top-0 z-50 flex items-center gap-4 px-7 h-[60px] bg-base/95 backdrop-blur-md border-b border-border">

      {/* Logo */}
      <button
        onClick={handleLogoClick}
        className="font-display text-[26px] tracking-widest text-gradient-logo whitespace-nowrap select-none border-none bg-transparent cursor-pointer"
      >
        ⚡ SPORTIFY
      </button>

      <div className="w-px h-7 bg-border2 shrink-0 hidden md:block" />

      {/* Nav Links — only show when logged in */}
      {user && (
        <div className="hidden md:flex gap-0.5">
          {["Home", "Matches", "Teams", "Standings", "Players", "Events"].map(label => {
            const route = "/" + label.toLowerCase();
            return (
              <button
                key={label}
                onClick={() => navigate(route)}
                className={`px-3.5 py-1.5 rounded-md text-[13.5px] font-medium border-none cursor-pointer transition-all duration-200
                  ${window.location.pathname === route ? "text-t1 bg-hover" : "text-t2 bg-transparent hover:text-t1 hover:bg-hover"}`}
              >
                {label}
              </button>
            );
          })}
        </div>
      )}

      {/* Search */}
      {user && (
        <div className="hidden md:flex ml-auto items-center gap-2.5 bg-card2 border border-border2 rounded-lg px-3.5 h-[38px] min-w-[200px] focus-within:border-accent transition-colors duration-200">
          <span className="text-t3 text-sm shrink-0">🔍</span>
          <input
            value={searchQ}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQ(e.target.value)}
            placeholder="Search…"
            className="bg-transparent border-none outline-none text-t1 text-[13.5px] w-full font-body placeholder:text-t3"
          />
        </div>
      )}

      {/* Right section */}
      <div className={`flex items-center gap-2 ${user ? "" : "ml-auto"} shrink-0`}>
        {user ? (
          <>
            {/* Notification */}
            <div className="relative w-9 h-9 rounded-lg bg-card border border-border flex items-center justify-center cursor-pointer text-t2 text-lg hover:border-accent hover:text-t1 transition-all duration-150">
              🔔
              <span className="absolute top-[7px] right-[7px] w-[7px] h-[7px] rounded-full bg-live border-[1.5px] border-base" />
            </div>

            {/* Avatar — click to go to profile */}
            <button
              onClick={handleProfile}
              className="w-9 h-9 rounded-lg bg-accent/20 border border-accent/40 flex items-center justify-center cursor-pointer font-heading font-bold text-accent-light text-sm hover:bg-accent/30 transition-all duration-150"
              title="My Profile"
            >
              {user.avatarInitial}
            </button>

            {/* Sign out */}
            <button
              onClick={handleSignOut}
              className="px-3 py-1.5 rounded-btn text-[12px] font-medium border border-border bg-transparent text-t3 cursor-pointer font-body transition-all duration-200 hover:border-live hover:text-live"
              title="Sign out"
            >
              ⏻
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => navigate("/login")}
              className="px-4 py-1.5 rounded-btn text-[13px] font-medium border border-border2 bg-transparent text-t2 cursor-pointer font-body transition-all duration-200 hover:border-accent hover:text-t1"
            >
              Log In
            </button>
            <button
              onClick={() => navigate("/signup")}
              className="px-4 py-1.5 rounded-btn text-[13px] font-semibold bg-accent text-white border-none cursor-pointer font-body transition-all duration-200 hover:bg-accent-light hover:-translate-y-px hover:shadow-accent-glow"
            >
              Sign Up
            </button>
          </>
        )}
      </div>
    </nav>
  );
}
