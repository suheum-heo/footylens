/**
 * Renders a form string like "WWDLW" as a row of coloured chips.
 * Most recent result is last (rightmost).
 */

const colorMap: Record<string, string> = {
  W: "bg-emerald-600 text-white",
  D: "bg-amber-500 text-white",
  L: "bg-red-600 text-white",
};

export default function FormBadge({ form }: { form: string }) {
  return (
    <span className="flex gap-0.5">
      {form.split("").map((result, i) => (
        <span
          key={i}
          className={[
            "inline-flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold",
            colorMap[result] ?? "bg-zinc-600 text-white",
          ].join(" ")}
        >
          {result}
        </span>
      ))}
    </span>
  );
}
