/**
 * /analytics — xG proxy bar chart + top scorers table.
 *
 * Data flow:
 *   getXG(PL, 38)       → per-match xG proxy values (matchday 38)
 *   getTopScorers(PL)   → ranked scorer list
 *
 * xG chart: horizontal split-bar per match.
 *   Home bar extends left from centre, away bar extends right.
 *   Width is proportional to xG relative to max(xG) in the dataset.
 */

import { getXG, getTopScorers } from "@/lib/api";

const XG_MATCHDAY = 38;

function XGBar({
  homeXG,
  awayXG,
  maxXG,
}: {
  homeXG: number;
  awayXG: number;
  maxXG: number;
}) {
  const homeW = Math.round((homeXG / maxXG) * 100);
  const awayW = Math.round((awayXG / maxXG) * 100);

  return (
    <div className="flex items-center gap-2 w-full">
      {/* Home bar (right-aligned) */}
      <div className="flex-1 flex justify-end">
        <div
          className="h-4 rounded-l bg-blue-600"
          style={{ width: `${homeW}%` }}
        />
      </div>
      {/* Away bar (left-aligned) */}
      <div className="flex-1">
        <div
          className="h-4 rounded-r bg-amber-500"
          style={{ width: `${awayW}%` }}
        />
      </div>
    </div>
  );
}

export default async function AnalyticsPage() {
  const [xgData, scorersData] = await Promise.all([
    getXG("PL", XG_MATCHDAY),
    getTopScorers("PL", 20),
  ]);

  const maxXG =
    xgData && xgData.matches.length > 0
      ? Math.max(...xgData.matches.flatMap((m) => [m.home_xg, m.away_xg]))
      : 1;

  return (
    <div className="flex flex-col gap-10">
      {/* ── xG Section ──────────────────────────────────────────────── */}
      <section>
        <div className="mb-4">
          <h1 className="text-xl font-semibold text-white">
            xG Proxy — Matchday {XG_MATCHDAY}
          </h1>
          {xgData && (
            <p className="mt-1 text-xs text-zinc-500">{xgData.note}</p>
          )}
        </div>

        {xgData && xgData.matches.length > 0 ? (
          <div className="rounded-lg border border-zinc-800 overflow-hidden">
            {/* Legend */}
            <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900 px-4 py-2 text-xs text-zinc-400">
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-sm bg-blue-600" />
                Home xG
              </span>
              <span className="flex items-center gap-1.5">
                Away xG
                <span className="h-3 w-3 rounded-sm bg-amber-500" />
              </span>
            </div>

            {xgData.matches.map((match, idx) => (
              <div
                key={match.match_id}
                className={[
                  "px-4 py-3",
                  idx > 0 && "border-t border-zinc-800/60",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {/* Team names + actual score */}
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="font-medium text-zinc-200">
                    {match.home_team_name}
                  </span>
                  <span className="text-zinc-500 text-xs">
                    {match.home_goals != null && match.away_goals != null
                      ? `${match.home_goals}–${match.away_goals}`
                      : match.status ?? "—"}
                  </span>
                  <span className="font-medium text-zinc-200">
                    {match.away_team_name}
                  </span>
                </div>

                {/* Bar chart */}
                <XGBar
                  homeXG={match.home_xg}
                  awayXG={match.away_xg}
                  maxXG={maxXG}
                />

                {/* xG values */}
                <div className="flex justify-between mt-1 text-xs text-zinc-500 tabular-nums">
                  <span>{match.home_xg.toFixed(2)}</span>
                  <span>{match.away_xg.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-6 py-10 text-center text-zinc-500 text-sm">
            No xG data for matchday {XG_MATCHDAY}. Run the sync command or wait
            for the season to reach this matchday.
          </div>
        )}
      </section>

      {/* ── Top Scorers Section ──────────────────────────────────────── */}
      <section>
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">Top Scorers</h2>
          <p className="text-sm text-zinc-400 mt-1">Premier League</p>
        </div>

        {scorersData && scorersData.scorers.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border border-zinc-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800 bg-zinc-900 text-zinc-400 text-xs uppercase tracking-wide">
                  <th className="px-3 py-3 text-right w-8">#</th>
                  <th className="px-4 py-3 text-left">Player</th>
                  <th className="px-4 py-3 text-left">Club</th>
                  <th className="px-3 py-3 text-right">G</th>
                  <th className="px-3 py-3 text-right">A</th>
                  <th className="px-3 py-3 text-right">P</th>
                  <th className="px-3 py-3 text-right">G/90</th>
                </tr>
              </thead>
              <tbody>
                {scorersData.scorers.map((scorer, idx) => (
                  <tr
                    key={scorer.player_id ?? idx}
                    className="border-b border-zinc-800/50 hover:bg-zinc-900/50 transition-colors"
                  >
                    <td className="px-3 py-3 text-right text-zinc-500 tabular-nums">
                      {scorer.rank}
                    </td>
                    <td className="px-4 py-3 font-medium text-white">
                      {scorer.player_name}
                    </td>
                    <td className="px-4 py-3 text-zinc-400">
                      {scorer.team_name}
                    </td>
                    <td className="px-3 py-3 text-right font-bold tabular-nums text-white">
                      {scorer.goals}
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums text-zinc-300">
                      {scorer.assists ?? "—"}
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums text-zinc-400">
                      {scorer.played_matches}
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums text-zinc-400">
                      {scorer.goals_per_game.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-6 py-10 text-center text-zinc-500 text-sm">
            No scorer data. Make sure the FastAPI service is running.
          </div>
        )}
      </section>
    </div>
  );
}
