import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Nav from "@/components/Nav";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FootyLens",
  description: "Football match analysis dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={geist.className}>
      <body className="min-h-screen bg-zinc-950 text-zinc-100">
        <div className="flex min-h-screen flex-col md:flex-row">
          {/* Sidebar — desktop only */}
          <aside className="hidden md:flex w-48 shrink-0 flex-col border-r border-zinc-800 bg-zinc-900">
            <div className="border-b border-zinc-800 px-4 py-5">
              <span className="text-base font-semibold tracking-tight text-white">
                FootyLens
              </span>
            </div>
            <Nav />
          </aside>

          {/* Mobile header with horizontal nav */}
          <header className="flex md:hidden items-center gap-2 border-b border-zinc-800 bg-zinc-900 px-4 py-3">
            <span className="text-sm font-semibold text-white mr-2">FootyLens</span>
            <Nav />
          </header>

          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
