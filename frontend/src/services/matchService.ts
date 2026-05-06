import axios from "axios";

const API_BASE = "http://localhost:5000/api/v1";

export interface Match {
  id: string;
  league_id: number;
  home_team_id: number;
  away_team_id: number;
  home_team?: { id: number; name: string; logo_url?: string };
  away_team?: { id: number; name: string; logo_url?: string };
  league?: { name: string; sport?: { name: string } };
  match_date: string;
  start_time?: string;
  status: "scheduled" | "live" | "finished";
  home_score?: number;
  away_score?: number;
  venue?: string;
  sport_id?: number;
}

export async function getLiveMatches(): Promise<Match[]> {
  try {
    const response = await axios.get(`${API_BASE}/matches/live`);
    return response.data.data || response.data;
  } catch (error: any) {
    console.error("Error fetching live matches:", error.message);
    throw error;
  }
}

export async function getMatches(params?: {
  status?: "scheduled" | "live" | "finished";
  sport?: string;
  league_id?: number;
  limit?: number;
  page?: number;
}): Promise<{ data: Match[]; meta?: any }> {
  try {
    const response = await axios.get(`${API_BASE}/matches`, { params });
    return {
      data: response.data.data || response.data,
      meta: response.data.meta,
    };
  } catch (error: any) {
    console.error("Error fetching matches:", error.message);
    throw error;
  }
}

export async function getMatchDetail(id: string): Promise<Match> {
  try {
    const response = await axios.get(`${API_BASE}/matches/${id}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching match detail:", error.message);
    throw error;
  }
}
