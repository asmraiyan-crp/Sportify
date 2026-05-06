import axios from "axios";

const API_BASE = "http://localhost:5000/api/v1";

export interface League {
  id: number;
  name: string;
  sport_id?: number;
  season?: string;
  country?: string;
  logo_url?: string;
}

export interface Standing {
  team_id: number;
  team_name: string;
  team_logo_url?: string;
  matches_played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
}

export async function getLeagues(params?: { sport_id?: number }): Promise<{ data: League[] }> {
  try {
    const response = await axios.get(`${API_BASE}/leagues`, { params });
    return {
      data: response.data.data || response.data,
    };
  } catch (error: any) {
    console.error("Error fetching leagues:", error.message);
    throw error;
  }
}

export async function getLeagueDetail(id: number): Promise<League> {
  try {
    const response = await axios.get(`${API_BASE}/leagues/${id}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching league detail:", error.message);
    throw error;
  }
}

export async function getLeagueStandings(id: number): Promise<{ data: Standing[] }> {
  try {
    const response = await axios.get(`${API_BASE}/leagues/${id}/standings`);
    return {
      data: response.data.standings || response.data.data || response.data,
    };
  } catch (error: any) {
    console.error("Error fetching league standings:", error.message);
    throw error;
  }
}
