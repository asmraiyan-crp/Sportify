import { useState, useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import type { AuthUser } from "./types";
import { useSearch }  from "./hooks";
import { getAuthToken, logout, getCurrentUser } from "./utils/auth";

import { Navbar }          from "./components/layout/Navbar";
import { Sidebar, Footer } from "./components/layout/Sidebar";
import { LandingPage }     from "./pages/LandingPage";
import { LoginPage }       from "./pages/LoginPage";
import { HomePage }        from "./pages/HomePage";
import { MatchesPage }     from "./pages/MatchesPage";
import { TeamsPage }       from "./pages/TeamsPage";
import { TeamDetailPage }  from "./pages/TeamDetailPage";
import { StandingsPage }   from "./pages/StandingsPage";
import { PlayersPage }     from "./pages/PlayersPage";
import { EventsPage }      from "./pages/EventsPage";
import { ProfilePage }     from "./pages/ProfilePage";
import { SignupPage }      from "./pages/SignupPage";

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const { query, setQuery } = useSearch();

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAuthToken();
      console.log("Auth check - Token found:", !!token);
      if (token) {
        try {
          console.log("Fetching current user...");
          const userData = await getCurrentUser();
          console.log("Current user data:", userData);
          setUser({
            id: userData.id,
            email: userData.email,
            displayName: userData.display_name || "User",
            avatarInitial: (userData.display_name || "A").charAt(0).toUpperCase(),
            role: userData.role as any,
            teamManaged: userData.team_managed || null,
            joinedAt: userData.created_at,
            followedTeams: [],
            followedPlayers: [],
          });
        } catch (error: any) {
          console.error("Failed to get current user:", error.message || error);
          // Token might be invalid, clear it
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleSignOut = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Logout error:", error);
    }
    setUser(null);
  };

  // Show loading screen while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-base">
        <div className="text-center">
          <div className="text-4xl mb-4">⚡</div>
          <p className="text-t3 font-body">Loading...</p>
        </div>
      </div>
    );
  }

  // ── Unauthenticated routes ────────────────────────────────────────────────
  if (!user) {
    return (
      <>
        <div className="h-[2px] bg-top-glow shrink-0" />
        <Navbar
          activePage="landing"
          setActivePage={() => {}}
          searchQ={query}
          setSearchQ={setQuery}
          user={null}
          onLogin={() => {}}
          onProfile={() => {}}
          onSignOut={() => {}}
          onSignup={() => {}}
        />
        <Routes>
          <Route path="/landing" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="*" element={<Navigate to="/landing" replace />} />
        </Routes>
      </>
    );
  }

  // ── Authenticated routes ──────────────────────────────────────────────────
  return (
    <div className="flex flex-col min-h-screen bg-base text-t1 font-body overflow-x-hidden">
      <div className="h-[2px] bg-top-glow shrink-0" />

      <Navbar
        activePage="home"
        setActivePage={() => {}}
        searchQ={query}
        setSearchQ={setQuery}
        user={user}
        onLogin={() => {}}
        onSignup={() => {}}
        onProfile={() => {}}
        onSignOut={handleSignOut}
      />

      <div className="flex flex-1 min-h-0">
        <main className="flex-1 min-w-0 px-7 py-6 overflow-y-auto">
          <Routes>
            <Route path="/home" element={<HomePage />} />
            <Route path="/matches" element={<MatchesPage />} />
            <Route path="/teams" element={<TeamsPage />} />
            <Route path="/teams/:id" element={<TeamDetailPage />} />
            <Route path="/standings" element={<StandingsPage />} />
            <Route path="/players" element={<PlayersPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/profile" element={<ProfilePage user={user} onBack={() => window.history.back()} />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        </main>

        <Sidebar activePage="home" onNav={() => {}} />
      </div>

      <Footer />
    </div>
  );
}
