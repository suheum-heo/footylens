/**
 * / — League standings with last-5 form badges.
 *
 * Data flow:
 *   getStandings(PL) → position table
 *   getForm(PL, 5)   → form string per team (matched by team_id)
 */

export const dynamic = "force-dynamic";

import { getStandings, getForm } from "@/lib/api";
import FormBadge from "@/components/FormBadge";

export default async function StandingsPage() {
  const [standingsData, formData] = await Promise.all([
    getStandings("PL"),
    getForm("PL", 5),
  ]);

  const formMap = new Map(
    formData?.teams.map((t) => [t.team_id, t.form]) ?? []
  );

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-white">Premier League</h1>
        <p className="text-sm text-zinc-400 mt-1">
          {standingsData
            ? `${standingsData.standings.length} clubs`
            : "Live standings unavailable — check FastAPI service"}
        </p>
      </div>

      {standingsData ? (
        <div className="overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900 text-zinc-400 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 text-right w-8">#</th>
                <th className="px-4 py-3 text-left">Club</th>
                <th className="px-3 py-3 text-right">P</th>
                <th className="px-3 py-3 text-right">W</th>
                <th className="px-3 py-3 text-right">D</th>
                <th className="px-3 py-3 text-right">L</th>
                <th className="px-3 py-3 text-right">GD</th>
                <th className="px-3 py-3 text-right font-bold text-white">Pts</th>
                <th className="px-4 py-3 text-left">Form</th>
              </tr>
            </thead>
            <tbody>
              {standingsData.standings.map((team, idx) => (
                <tr
                  key={team.teamId}
                  className={[
                    "border-b border-zinc-800/50 transition-colors hover:bg-zinc-900/50",
                    idx < 4 ? "border-l-2 border-l-blue-500" : "",
                    idx === 4 ? "border-l-2 border-l-amber-500" : "",
                    idx >= standingsData.standings.length - 3
                      ? "border-l-2 border-l-red-600"
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <td className="px-4 py-3 text-right text-zinc-400 tabular-nums">
                    {team.position}
                  </td>
                  <td className="px-4 py-3 font-medium text-white">
                    {team.teamName}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-zinc-300">
                    {team.playedGames}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-zinc-300">
                    {team.wins}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-zinc-300">
                    {team.draws}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-zinc-300">
                    {team.losses}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums text-zinc-300">
                    {team.goalDifference > 0
                      ? `+${team.goalDifference}`
                      : team.goalDifference}
                  </td>
                  <td className="px-3 py-3 text-right tabular-nums font-bold text-white">
                    {team.points}
                  </td>
                  <td className="px-4 py-3">
                    {formMap.has(team.teamId) ? (
                      <FormBadge form={formMap.get(team.teamId)!} />
                    ) : (
                      <span className="text-zinc-600 text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-6 py-12 text-center text-zinc-500">
          Could not load standings. Make sure the FastAPI service is running.
        </div>
      )}

      {standingsData && (
        <div className="mt-4 flex gap-4 text-xs text-zinc-500">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-1 rounded-full bg-blue-500" />
            Champions League
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-1 rounded-full bg-amber-500" />
            Europa League
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-1 rounded-full bg-red-600" />
            Relegation
          </span>
        </div>
      )}
    </div>
  );
}
