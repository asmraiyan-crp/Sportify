import { useState, useEffect } from "react";
import { SectionHeader, CapacityBar, EmptyState } from "../components/shared";
import { getEvents, registerForEvent, unregisterFromEvent } from "../services/eventService";
import type { FanEvent } from "../services/eventService";

export function EventsPage() {
  const [events, setEvents] = useState<FanEvent[]>([]);
  const [registered, setRegistered] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const res = await getEvents();
        setEvents(res.data);
      } catch (err: any) {
        console.error("Error fetching events:", err);
        setError(err.message || "Failed to load events");
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const handleRegister = async (eventId: string) => {
    try {
      await registerForEvent(eventId);
      setRegistered(prev => new Set([...prev, eventId]));
    } catch (err: any) {
      console.error("Error registering for event:", err);
    }
  };

  const handleUnregister = async (eventId: string) => {
    try {
      await unregisterFromEvent(eventId);
      setRegistered(prev => {
        const newSet = new Set(prev);
        newSet.delete(eventId);
        return newSet;
      });
    } catch (err: any) {
      console.error("Error unregistering from event:", err);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚡</div>
        <p className="text-t3">Loading events...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-live mb-4">⚠️ {error}</p>
        <button onClick={() => window.location.reload()} className="text-accent-light hover:underline">
          Try again
        </button>
      </div>
    );
  }

  return (
    <>
      <SectionHeader title="Fan Events" />
      {events.length > 0 ? (
        <div className="flex flex-col gap-4 mb-9">
          {events.map((ev: FanEvent) => {
            const isRegistered = registered.has(ev.event_id);
            const isFull = (ev.registered || 0) >= ev.capacity;
            const date = new Date(ev.event_date);

            return (
              <div key={ev.event_id} className="bg-card border border-border rounded-card p-5 hover:border-border2 transition-all duration-200">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-heading text-[17px] font-bold text-t1 mb-1">{ev.title}</h3>
                    <p className="text-[13px] text-t3">{ev.description}</p>
                  </div>
                  <div className="text-right shrink-0 bg-card2 border border-border rounded-lg px-3 py-2">
                    <div className="font-heading text-[24px] font-bold text-accent-light leading-none">
                      {ev.registered || 0}
                    </div>
                    <div className="text-[11px] text-t3">/ {ev.capacity}</div>
                  </div>
                </div>

                <div className="flex items-center gap-5 mb-4 flex-wrap">
                  <span className="text-[12px] text-t2">
                    📅 {date.toLocaleDateString("en-GB", { weekday:"short", day:"numeric", month:"short" })}
                    {" · "}
                    {date.toLocaleTimeString("en-GB", { hour:"2-digit", minute:"2-digit" })}
                  </span>
                  <span className="text-[12px] text-t2">📍 {ev.location}</span>
                </div>

                <CapacityBar registered={ev.registered || 0} capacity={ev.capacity} />

                <button
                  onClick={() => isRegistered ? handleUnregister(ev.event_id) : handleRegister(ev.event_id)}
                  className={`w-full mt-4 py-2 rounded-btn text-[12px] font-semibold font-heading tracking-wide border transition-all duration-200
                    ${isRegistered
                      ? "bg-accent/20 text-accent-light border-accent/40 cursor-pointer hover:bg-accent/30"
                      : isFull
                      ? "bg-border text-t3 border-border cursor-not-allowed"
                      : "bg-accent text-white border-accent hover:bg-accent-light active:scale-[0.98]"}`}
                  disabled={isFull && !isRegistered}
                >
                  {isRegistered ? "✓ Registered" : isFull ? "Event Full" : "Register Now"}
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState icon="🎪" message="No upcoming events." />
      )}
    </>
  );
}
