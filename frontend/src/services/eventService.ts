import axios from "axios";

const API_BASE = "http://localhost:5000/api/v1";

export interface FanEvent {
  event_id: string;
  title: string;
  description?: string;
  event_date: string;
  location?: string;
  capacity: number;
  registered?: number;
  spots_left?: number;
  created_by?: string;
}

export async function getEvents(params?: { limit?: number; page?: number }): Promise<{ data: FanEvent[] }> {
  try {
    const response = await axios.get(`${API_BASE}/events`, { params });
    return {
      data: response.data.data || response.data,
    };
  } catch (error: any) {
    console.error("Error fetching events:", error.message);
    throw error;
  }
}

export async function getEventDetail(id: string): Promise<FanEvent> {
  try {
    const response = await axios.get(`${API_BASE}/events/${id}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching event detail:", error.message);
    throw error;
  }
}

export async function registerForEvent(id: string): Promise<any> {
  try {
    const response = await axios.post(`${API_BASE}/events/${id}/register`);
    return response.data;
  } catch (error: any) {
    console.error("Error registering for event:", error.message);
    throw error;
  }
}

export async function unregisterFromEvent(id: string): Promise<any> {
  try {
    const response = await axios.delete(`${API_BASE}/events/${id}/register`);
    return response.data;
  } catch (error: any) {
    console.error("Error unregistering from event:", error.message);
    throw error;
  }
}
