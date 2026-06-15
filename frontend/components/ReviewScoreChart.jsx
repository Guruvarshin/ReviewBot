"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function ReviewScoreChart({ overallScore, dimensionScores }) {
  const data = [
    { name: "Overall", score: overallScore },
    { name: "Security", score: dimensionScores.security },
    { name: "Performance", score: dimensionScores.performance },
    { name: "Quality", score: dimensionScores.quality },
    { name: "Testing", score: dimensionScores.testing },
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Line type="monotone" dataKey="score" name="Score" stroke="#4f46e5" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
