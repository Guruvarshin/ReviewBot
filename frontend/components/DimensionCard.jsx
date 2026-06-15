import FindingItem from "./FindingItem";
import ScoreBadge from "./ScoreBadge";

const DIMENSION_META = {
  security: { label: "Security", icon: "🔒" },
  performance: { label: "Performance", icon: "⚡" },
  quality: { label: "Code Quality", icon: "🧹" },
  testing: { label: "Testing", icon: "🧪" },
};

export default function DimensionCard({ dimension, result }) {
  const meta = DIMENSION_META[dimension];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 font-semibold text-slate-900">
          <span>{meta.icon}</span> {meta.label}
        </h3>
        {result ? (
          <ScoreBadge score={result.score} size="sm" />
        ) : (
          <div className="h-10 w-10 animate-pulse rounded-full bg-slate-100" />
        )}
      </div>

      {!result && <p className="mt-3 text-sm text-slate-400">Analyzing…</p>}

      {result && (
        <>
          <p className="mt-3 text-sm text-slate-600">{result.summary}</p>
          {result.findings.length === 0 ? (
            <p className="mt-3 text-sm text-slate-400">No issues found.</p>
          ) : (
            <div className="mt-3 space-y-2">
              {result.findings.map((finding, i) => (
                <FindingItem key={i} finding={finding} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
