"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const SERIES = [
  { key: "overall_score", label: "Overall", color: "#4f46e5" },
  { key: "security", label: "Security", color: "#dc2626" },
  { key: "performance", label: "Performance", color: "#059669" },
  { key: "quality", label: "Quality", color: "#d97706" },
  { key: "testing", label: "Testing", color: "#7c3aed" },
];

export default function TrendChart({ reviews }) {
  const data = reviews.map((review) => ({
    created_at: new Date(review.created_at).toLocaleDateString(),
    pr_number: review.pr_number,
    overall_score: review.overall_score,
    ...review.dimension_scores,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="created_at" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Legend />
        {SERIES.map((series) => (
          <Line
            key={series.key}
            type="monotone"
            dataKey={series.key}
            name={series.label}
            stroke={series.color}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
