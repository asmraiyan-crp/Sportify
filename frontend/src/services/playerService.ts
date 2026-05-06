import axios from "axios";

const API_BASE = "http://localhost:5000/api/v1";

export interface Player {
  id: string;
  name: string;
  sport_id?: number;
  team_id?: number;
  team?: { id: number; name: string; logo_url?: string };
  position?: string;
  jersey_number?: number;
  height_cm?: number;
  weight_kg?: number;
  date_of_birth?: string;
  country?: string;
  injury_status?: "active" | "injured" | "out";
}

export async function getPlayers(params?: {
  sport_id?: number;
  team_id?: number;
  name?: string;
  limit?: number;
  page?: number;
}): Promise<{ data: Player[]; meta?: any }> {
  try {
    const response = await axios.get(`${API_BASE}/players`, { params });
    return {
      data: response.data.data || response.data,
      meta: response.data.meta,
    };
  } catch (error: any) {
    console.error("Error fetching players:", error.message);
    throw error;
  }
}

export async function getPlayerDetail(id: string): Promise<Player> {
  try {
    const response = await axios.get(`${API_BASE}/players/${id}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching player detail:", error.message);
    throw error;
  }
}

export async function getPlayerStats(id: string): Promise<any> {
  try {
    const response = await axios.get(`${API_BASE}/players/${id}/stats`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching player stats:", error.message);
    throw error;
  }
}
