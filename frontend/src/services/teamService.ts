import axios from "axios";

const API_BASE = "http://localhost:5000/api/v1";

export interface Team {
  id: number;
  name: string;
  sport_id?: number;
  league_id?: number;
  logo_url?: string;
  country?: string;
  founded_year?: number;
  home_ground?: string;
  coach?: string;
}

export async function getTeams(params?: {
  sport_id?: number;
  league_id?: number;
  limit?: number;
  page?: number;
}): Promise<{ data: Team[]; meta?: any }> {
  try {
    const response = await axios.get(`${API_BASE}/teams`, { params });
    return {
      data: response.data.data || response.data,
      meta: response.data.meta,
    };
  } catch (error: any) {
    console.error("Error fetching teams:", error.message);
    throw error;
  }
}

export async function getTeamDetail(id: number): Promise<Team> {
  try {
    const response = await axios.get(`${API_BASE}/teams/${id}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching team detail:", error.message);
    throw error;
  }
}

export async function getTeamSquad(id: number): Promise<any[]> {
  try {
    const response = await axios.get(`${API_BASE}/teams/${id}/squad`);
    return response.data.data || response.data;
  } catch (error: any) {
    console.error("Error fetching team squad:", error.message);
    throw error;
  }
}
