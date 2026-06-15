"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [prUrl, setPrUrl] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = prUrl.trim();
    if (!trimmed) return;
    router.push(`/review?pr_url=${encodeURIComponent(trimmed)}`);
  }

  return (
    <main className="flex min-h-[80vh] flex-col items-center justify-center px-8">
      <div className="w-full max-w-xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">ReviewBot</h1>
        <p className="mt-3 text-lg text-slate-500">
          AI-powered code review for any public GitHub pull request.
        </p>
        <form onSubmit={handleSubmit} className="mt-8 flex gap-2">
          <input
            type="text"
            value={prUrl}
            onChange={(e) => setPrUrl(e.target.value)}
            placeholder="https://github.com/owner/repo/pull/123"
            className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />
          <button
            type="submit"
            className="rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            Review
          </button>
        </form>
        <p className="mt-4 text-xs text-slate-400">
          Runs 4 specialist AI agents in parallel: security, performance, quality, and testing.
        </p>
      </div>
    </main>
  );
}
