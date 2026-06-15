import DimensionCard from "@/components/DimensionCard";
import ReviewScoreChart from "@/components/ReviewScoreChart";
import ScoreBadge from "@/components/ScoreBadge";

const DIMENSIONS = ["security", "performance", "quality", "testing"];

async function getReview(id) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const res = await fetch(`${apiUrl}/api/reviews/${id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export default async function ReviewDetailPage({ params }) {
  const review = await getReview(params.id);

  if (!review) {
    return (
      <main className="mx-auto max-w-4xl px-8 py-8">
        <a href="/history" className="text-sm font-medium text-indigo-600 hover:underline">← All reviews</a>
        <p className="mt-4 text-sm text-slate-400">Review not found.</p>
      </main>
    );
  }

  const agentResults = {};
  for (const result of review.agent_results) {
    agentResults[result.dimension] = result;
  }

  return (
    <main className="mx-auto max-w-4xl px-8 py-8">
      <a href="/history" className="text-sm font-medium text-indigo-600 hover:underline">← All reviews</a>

      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900">{review.pr_title}</h1>
        <p className="mt-1 text-sm text-slate-500">
          <a href={review.pr_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
            #{review.pr_number}
          </a>{" "}
          in{" "}
          <a href={`/repo/${review.repo_owner}/${review.repo_name}`} className="text-indigo-600 hover:underline">
            {review.repo_owner}/{review.repo_name}
          </a>{" "}
          · {new Date(review.created_at).toLocaleString()}
        </p>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-4">
          <ScoreBadge score={review.overall_score} size="lg" />
          <div>
            <div className="text-sm font-semibold text-slate-900">Overall score</div>
            <div className="text-xs text-slate-400">Completed in {review.review_duration_seconds.toFixed(1)}s</div>
          </div>
        </div>
        <p className="mt-4 text-sm text-slate-600">{review.consolidated_summary}</p>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="px-1 text-sm font-semibold text-slate-900">Score breakdown</h2>
        <ReviewScoreChart overallScore={review.overall_score} dimensionScores={review.dimension_scores} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {DIMENSIONS.map((dimension) => (
          <DimensionCard key={dimension} dimension={dimension} result={agentResults[dimension]} />
        ))}
      </div>
    </main>
  );
}
