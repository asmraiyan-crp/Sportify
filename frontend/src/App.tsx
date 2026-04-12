import { useState } from "react";
import type { Page, AuthUser } from "./types";
import { MOCK_USER } from "./data";
import { useSearch }  from "./hooks";

import { Navbar }          from "./components/layout/Navbar";
import { Sidebar, Footer } from "./components/layout/Sidebar";
import { LandingPage }     from "./pages/LandingPage";
import { DashboardPage }   from "./pages/DashboardPage";
import { ProfilePage }     from "./pages/ProfilePage";
import { SignupPage } from "./pages/SignupPage";

export default function App() {
  // ── Auth state ────────────────────────────────────────────────────────────
  // Replace MOCK_USER with a real axios.post('/api/v1/auth/login') call when
  // your Flask backend is ready. See README.md for the wiring guide.
  const [user, setUser] = useState<AuthUser | null>(null);

  // ── Page routing ──────────────────────────────────────────────────────────
  const [page, setPage] = useState<Page>("landing");

  // ── Global search ─────────────────────────────────────────────────────────
  const { query, setQuery } = useSearch();

  // ── Auth actions ──────────────────────────────────────────────────────────
  const handleLogin = () => {
    // TODO: replace with real Flask auth call + JWT storage
    setUser(MOCK_USER);
    setPage("home");
  };


  const handleSignOut = () => {
    setUser(null);
    setPage("landing");
  };

  // ── Navigation helpers ────────────────────────────────────────────────────
  const goToProfile = () => setPage("profile");
  const goBack      = () => setPage("home");
  const goToSignup  = () => setPage("signup");

  // ── Landing (unauthenticated) ─────────────────────────────────────────────
  if (!user || page === "landing") {
    return (
      <>
        <div className="h-[2px] bg-top-glow shrink-0" />
        <Navbar
          activePage="landing"
          setActivePage={setPage}
          searchQ={query}
          setSearchQ={setQuery}
          user={null}
          onLogin={handleLogin}
          onProfile={goToProfile}
          onSignOut={handleSignOut}
          onSignup={goToSignup}
        />
        {page === "signup" ? (
          <SignupPage />
        ) : (
          <LandingPage onGetStarted={handleLogin} />
        )}
      </>
    );
  }

  // ── Authenticated shell ───────────────────────────────────────────────────
  return (
    <div className="flex flex-col min-h-screen bg-base text-t1 font-body overflow-x-hidden">
      <div className="h-[2px] bg-top-glow shrink-0" />

      <Navbar
        activePage={page}
        setActivePage={setPage}
        searchQ={query}
        setSearchQ={setQuery}
        user={user}
        onLogin={handleLogin}
        onSignup={goToSignup}
        onProfile={goToProfile}
        onSignOut={handleSignOut}
      />

      <div className="flex flex-1 min-h-0">
        <main className="flex-1 min-w-0 px-7 py-6 overflow-y-auto">
          {page === "profile" ? (
            <ProfilePage user={user} onBack={goBack} />
          ) : (
            <DashboardPage />
          )}
        </main>

        {page !== "profile" && (
          <Sidebar activePage={page} onNav={setPage} />
        )}
      </div>

      <Footer />
    </div>
  );
}
