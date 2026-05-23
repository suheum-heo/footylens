"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Standings" },
  { href: "/matches", label: "Matches" },
  { href: "/analytics", label: "Analytics" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-row md:flex-col gap-1 p-2 md:p-4">
      {links.map(({ href, label }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={[
              "rounded px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-white/10 text-white"
                : "text-zinc-400 hover:bg-white/5 hover:text-white",
            ].join(" ")}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
