"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import DimensionCard from "@/components/DimensionCard";
import ScoreBadge from "@/components/ScoreBadge";

const DIMENSIONS = ["security", "performance", "quality", "testing"];

function ReviewContent() {
  const searchParams = useSearchParams();
  const prUrl = searchParams.get("pr_url") ?? "";

  const [prInfo, setPrInfo] = useState(null);
  const [staticInfo, setStaticInfo] = useState(null);
  const [agentResults, setAgentResults] = useState({});
  const [finalReview, setFinalReview] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!prUrl) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const source = new EventSource(
      `${apiUrl}/api/review/stream?pr_url=${encodeURIComponent(prUrl)}`
    );

    source.addEventListener("pr_fetched", (event) => {
      setPrInfo(JSON.parse(event.data));
    });

    source.addEventListener("static_analysis_complete", (event) => {
      setStaticInfo(JSON.parse(event.data));
    });

    source.addEventListener("agent_complete", (event) => {
      const result = JSON.parse(event.data);
      setAgentResults((prev) => ({ ...prev, [result.dimension]: result }));
    });

    source.addEventListener("review_complete", (event) => {
      setFinalReview(JSON.parse(event.data));
      source.close();
    });

    source.addEventListener("error", (event) => {
      if (event.data) {
        setError(JSON.parse(event.data).message);
      } else {
        setError("Lost connection to the server.");
      }
      source.close();
    });

    return () => source.close();
  }, [prUrl]);

  if (!prUrl) {
    return <p className="p-8">No PR URL provided.</p>;
  }

  return (
    <main className="mx-auto max-w-4xl px-8 py-8">
      <a href="/" className="text-sm font-medium text-indigo-600 hover:underline">
        ← New review
      </a>

      {error && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {prInfo ? (
        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h1 className="text-xl font-bold text-slate-900">{prInfo.title}</h1>
          <p className="mt-1 text-sm text-slate-500">
            by {prInfo.author} · {prInfo.head_branch} → {prInfo.base_branch} · {prInfo.changed_files} files
            (<span className="text-emerald-600">+{prInfo.additions}</span> / <span className="text-red-600">-{prInfo.deletions}</span>)
          </p>
          {staticInfo && (
            <p className="mt-2 text-xs text-slate-400">Static analysis: {staticInfo.python_files_analyzed} Python file(s) analyzed</p>
          )}
          <p className="mt-3 break-all text-xs text-slate-400">{prUrl}</p>
        </div>
      ) : (
        !error && (
          <div className="mt-4 animate-pulse rounded-xl border border-slate-200 bg-white p-5">
            <div className="h-5 w-2/3 rounded bg-slate-100" />
            <div className="mt-2 h-4 w-1/2 rounded bg-slate-100" />
          </div>
        )
      )}

      {finalReview && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-4">
            <ScoreBadge score={finalReview.overall_score} size="lg" />
            <div>
              <div className="text-sm font-semibold text-slate-900">Overall score</div>
              <div className="text-xs text-slate-400">Completed in {finalReview.review_duration_seconds.toFixed(1)}s</div>
            </div>
          </div>
          <p className="mt-4 text-sm text-slate-600">{finalReview.consolidated_summary}</p>
          <a href={`/repo/${finalReview.repo_owner}/${finalReview.repo_name}`} className="mt-3 inline-block text-sm font-medium text-indigo-600 hover:underline">
            View trend for {finalReview.repo_owner}/{finalReview.repo_name} →
          </a>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {DIMENSIONS.map((dimension) => (
          <DimensionCard key={dimension} dimension={dimension} result={agentResults[dimension]} />
        ))}
      </div>
    </main>
  );
}

export default function ReviewPage() {
  return (
    <Suspense fallback={<p className="p-8">Loading...</p>}>
      <ReviewContent />
    </Suspense>
  );
}
