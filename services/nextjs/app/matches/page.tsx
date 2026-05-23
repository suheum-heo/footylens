/**
 * /matches — Premier League fixtures and results.
 *
 * Data strategy:
 *   1. Fetch default window (today ± ~1 week).
 *   2. If empty (off-season / international break), fall back to all FINISHED
 *      matches and show only the most recently completed matchday.
 */

export const dynamic = "force-dynamic";

import { getMatches } from "@/lib/api";
import type { Match } from "@/types/api";

const STATUS_LABEL: Record<string, string> = {
  FINISHED: "FT",
  IN_PLAY: "LIVE",
  PAUSED: "HT",
  TIMED: "—",
  SCHEDULED: "—",
  POSTPONED: "PPD",
  SUSPENDED: "SUSP",
  CANCELLED: "CANC",
};

function formatDate(utcDate: string): string {
  return new Date(utcDate).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/London",
  });
}

function groupByMatchday(matches: Match[]): Map<number, Match[]> {
  const map = new Map<number, Match[]>();
  for (const m of matches) {
    const md = m.matchday ?? 0;
    if (!map.has(md)) map.set(md, []);
    map.get(md)!.push(m);
  }
  return map;
}

export default async function MatchesPage() {
  // 1. Try the default window (full season from competition endpoint).
  // 2. If empty, try the most recent finished matchday.
  // 3. If still empty, try upcoming (TIMED / SCHEDULED) fixtures.
  const windowData = await getMatches("PL");
  const hasWindow = (windowData?.matches.length ?? 0) > 0;

  let fallback: Awaited<ReturnType<typeof getMatches>> = null;
  if (!hasWindow) {
    fallback = await getMatches("PL", undefined, "FINISHED");
    if ((fallback?.matches.length ?? 0) === 0) {
      fallback = await getMatches("PL", undefined, "TIMED");
    }
    if ((fallback?.matches.length ?? 0) === 0) {
      fallback = await getMatches("PL", undefined, "SCHEDULED");
    }
  }

  const matches = hasWindow ? windowData!.matches : fallback?.matches ?? [];

  // Fallback: keep only the highest matchday so we don't dump the full season.
  const isFallback = !hasWindow && matches.length > 0;
  const displayMatches = isFallback
    ? (() => {
        const maxMd = Math.max(...matches.map((m) => m.matchday ?? 0));
        return matches.filter((m) => (m.matchday ?? 0) === maxMd);
      })()
    : matches;

  const byMatchday = groupByMatchday(displayMatches);
  // Most recent matchday first.
  const matchdays = Array.from(byMatchday.keys()).sort((a, b) => b - a);

  if (displayMatches.length === 0) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-white">Matches</h1>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-6 py-12 text-center text-zinc-500">
          No match data available. Make sure the FastAPI service is running.
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-white">Matches</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Premier League
          {isFallback && (
            <span className="ml-2 text-zinc-600">
              · matchday {matchdays[0]}
            </span>
          )}
        </p>
      </div>

      <div className="flex flex-col gap-6">
        {matchdays.map((md) => (
          <section key={md}>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-widest text-zinc-500">
              Matchday {md || "Unknown"}
            </h2>
            <div className="rounded-lg border border-zinc-800 overflow-hidden">
              {byMatchday.get(md)!.map((match, idx) => {
                const finished = match.status === "FINISHED";
                const live =
                  match.status === "IN_PLAY" || match.status === "PAUSED";
                const homeGoals = match.score?.fullTime?.home;
                const awayGoals = match.score?.fullTime?.away;

                return (
                  <div
                    key={match.id}
                    className={[
                      "flex items-center gap-3 px-4 py-3 text-sm",
                      idx > 0 && "border-t border-zinc-800/60",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    {/* Date */}
                    <span className="w-40 shrink-0 text-zinc-500 text-xs">
                      {formatDate(match.utcDate)}
                    </span>

                    {/* Home team */}
                    <span
                      className={[
                        "flex-1 text-right font-medium",
                        finished && homeGoals != null && awayGoals != null
                          ? homeGoals > awayGoals
                            ? "text-white"
                            : "text-zinc-400"
                          : "text-zinc-300",
                      ].join(" ")}
                    >
                      {match.homeTeamName}
                    </span>

                    {/* Score / status */}
                    <div className="flex w-20 shrink-0 items-center justify-center gap-1 text-center">
                      {finished && homeGoals != null && awayGoals != null ? (
                        <>
                          <span className="w-5 text-right font-bold tabular-nums text-white">
                            {homeGoals}
                          </span>
                          <span className="text-zinc-600">–</span>
                          <span className="w-5 text-left font-bold tabular-nums text-white">
                            {awayGoals}
                          </span>
                        </>
                      ) : (
                        <span
                          className={[
                            "text-xs font-semibold px-2 py-0.5 rounded",
                            live
                              ? "bg-green-600/20 text-green-400"
                              : "text-zinc-600",
                          ].join(" ")}
                        >
                          {STATUS_LABEL[match.status] ?? match.status}
                        </span>
                      )}
                    </div>

                    {/* Away team */}
                    <span
                      className={[
                        "flex-1 font-medium",
                        finished && homeGoals != null && awayGoals != null
                          ? awayGoals > homeGoals
                            ? "text-white"
                            : "text-zinc-400"
                          : "text-zinc-300",
                      ].join(" ")}
                    >
                      {match.awayTeamName}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
