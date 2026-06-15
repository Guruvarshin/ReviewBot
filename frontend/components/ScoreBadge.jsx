function scoreStyle(score) {
  if (score >= 85) return "text-emerald-600 bg-emerald-50 ring-emerald-200";
  if (score >= 70) return "text-amber-600 bg-amber-50 ring-amber-200";
  return "text-red-600 bg-red-50 ring-red-200";
}

const SIZES = {
  sm: "h-10 w-10 text-sm",
  md: "h-14 w-14 text-lg",
  lg: "h-20 w-20 text-2xl",
};

export default function ScoreBadge({ score, size = "md" }) {
  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-full font-bold ring-2 ${SIZES[size]} ${scoreStyle(score)}`}
    >
      {score}
    </div>
  );
}
