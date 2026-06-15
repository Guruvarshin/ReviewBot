import TrendChart from "@/components/TrendChart";

async function getTrend(owner, name) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const res = await fetch(`${apiUrl}/api/repo/${owner}/${name}/trend`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

export default async function RepoTrendPage({ params }) {
  const { owner, name } = params;
  const reviews = await getTrend(owner, name);

  return (
    <main className="mx-auto max-w-4xl px-8 py-8">
      <a href="/history" className="text-sm font-medium text-indigo-600 hover:underline">← All reviews</a>
      <h1 className="mt-2 text-2xl font-bold text-slate-900">{owner}/{name}</h1>
      <p className="text-sm text-slate-500">{reviews.length} review(s) recorded</p>

      {reviews.length === 0 ? (
        <p className="mt-6 text-sm text-slate-400">No reviews yet for this repository.</p>
      ) : (
        <>
          <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <TrendChart reviews={reviews} />
          </div>

          <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-500">
                  <th className="px-4 py-3 font-medium">PR</th>
                  <th className="px-4 py-3 font-medium">Overall</th>
                  <th className="px-4 py-3 font-medium">Security</th>
                  <th className="px-4 py-3 font-medium">Performance</th>
                  <th className="px-4 py-3 font-medium">Quality</th>
                  <th className="px-4 py-3 font-medium">Testing</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {reviews.slice().reverse().map((review, i) => (
                  <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <a href={review.pr_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                        #{review.pr_number} {review.pr_title}
                      </a>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-900">{review.overall_score}</td>
                    <td className="px-4 py-3 text-slate-600">{review.dimension_scores.security}</td>
                    <td className="px-4 py-3 text-slate-600">{review.dimension_scores.performance}</td>
                    <td className="px-4 py-3 text-slate-600">{review.dimension_scores.quality}</td>
                    <td className="px-4 py-3 text-slate-600">{review.dimension_scores.testing}</td>
                    <td className="px-4 py-3 text-slate-400">{new Date(review.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
