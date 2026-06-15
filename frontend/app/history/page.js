async function getReviews(repoOwner, repoName) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const params = new URLSearchParams();
  if (repoOwner) params.set("repo_owner", repoOwner);
  if (repoName) params.set("repo_name", repoName);

  const res = await fetch(`${apiUrl}/api/reviews?${params.toString()}`, {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

export default async function HistoryPage({ searchParams }) {
  const { repo_owner, repo_name } = searchParams;
  const reviews = await getReviews(repo_owner, repo_name);

  return (
    <main className="mx-auto max-w-4xl px-8 py-8">
      <a href="/" className="text-sm font-medium text-indigo-600 hover:underline">← New review</a>
      <h1 className="mt-2 text-2xl font-bold text-slate-900">Review History</h1>

      <form method="GET" className="mt-4 flex gap-2">
        <input type="text" name="repo_owner" defaultValue={repo_owner} placeholder="repo owner (e.g. psf)" className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        <input type="text" name="repo_name" defaultValue={repo_name} placeholder="repo name (e.g. requests)" className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700">Filter</button>
      </form>

      {reviews.length === 0 ? (
        <p className="mt-6 text-sm text-slate-400">No reviews recorded yet.</p>
      ) : (
        <div className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-500">
                <th className="px-4 py-3 font-medium">Repo</th>
                <th className="px-4 py-3 font-medium">PR</th>
                <th className="px-4 py-3 font-medium">Overall</th>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((review, i) => (
                <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <a href={`/repo/${review.repo_owner}/${review.repo_name}`} className="text-indigo-600 hover:underline">
                      {review.repo_owner}/{review.repo_name}
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <a href={review.pr_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                      #{review.pr_number} {review.pr_title}
                    </a>
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-900">{review.overall_score}</td>
                  <td className="px-4 py-3 text-slate-400">{new Date(review.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <a href={`/review/${review.id}`} className="font-medium text-indigo-600 hover:underline">
                      View →
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
