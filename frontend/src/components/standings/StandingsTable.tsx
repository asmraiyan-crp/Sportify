import type { Standing } from "../../types";
import { FormDots } from "../shared";

interface StandingsTableProps {
  rows:     Standing[];
  compact?: boolean;
}

export function StandingsTable({ rows, compact = false }: StandingsTableProps) {
  const cols = compact
    ? ["#", "Team", "P", "Pts", "Form"]
    : ["#", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts", "Form"];

  return (
    <table className="w-full border-collapse">
      <thead>
        <tr>
          {cols.map((h, i) => (
            <th key={h} className={`text-[10px] font-semibold text-t3 uppercase tracking-widest pb-2.5 px-1 ${i <= 1 ? "text-left" : "text-center"}`}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map(r => {
          const gd = r.gf - r.ga;
          return (
            <tr key={r.pos} className="border-t border-border hover:bg-hover/40 transition-colors duration-100 cursor-pointer">
              <td className={`py-2 px-1 text-[11px] font-bold text-center ${r.pos <= 4 ? "text-accent-light" : "text-t3"}`}>
                {r.pos}
              </td>
              <td className="py-2 px-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs shrink-0">{r.badge}</span>
                  <span className="font-heading text-sm font-bold text-t1 truncate">{r.team}</span>
                </div>
              </td>
              <td className="py-2 px-1 text-center text-[13px] text-t2">{r.played}</td>
              {!compact && (
                <>
                  <td className="py-2 px-1 text-center text-[13px] text-win">{r.won}</td>
                  <td className="py-2 px-1 text-center text-[13px] text-t2">{r.drawn}</td>
                  <td className="py-2 px-1 text-center text-[13px] text-live">{r.lost}</td>
                  <td className="py-2 px-1 text-center text-[13px] text-t2">{r.gf}</td>
                  <td className="py-2 px-1 text-center text-[13px] text-t2">{r.ga}</td>
                  <td className={`py-2 px-1 text-center text-[13px] font-semibold ${gd > 0 ? "text-win" : gd < 0 ? "text-live" : "text-t2"}`}>
                    {gd > 0 ? `+${gd}` : gd}
                  </td>
                </>
              )}
              <td className="py-2 px-1 text-center font-heading text-[15px] font-bold text-t1">{r.pts}</td>
              <td className="py-2 px-1">
                <div className="flex justify-center">
                  <FormDots form={r.form} />
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
