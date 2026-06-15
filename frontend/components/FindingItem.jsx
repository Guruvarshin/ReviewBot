"use client";

import { useState } from "react";
import SeverityBadge from "./SeverityBadge";

export default function FindingItem({ finding }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-100"
      >
        <SeverityBadge severity={finding.severity} />
        <span className="flex-1 truncate text-slate-700">{finding.title}</span>
        <span className="whitespace-nowrap text-xs text-slate-400">
          {finding.file}
          {finding.line ? `:${finding.line}` : ""}
        </span>
        <span className="w-3 text-center text-slate-400">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="border-t border-slate-200 px-3 py-2 text-sm text-slate-600">
          <p>{finding.description}</p>
          {finding.suggestion && (
            <p className="mt-2 text-slate-500">
              <span className="font-medium text-slate-700">Suggestion: </span>
              {finding.suggestion}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
