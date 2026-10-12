"use client"

import * as React from "react"
import Link from "next/link"
import { Loader2, ScrollText } from "lucide-react"

import { AppShell } from "@/components/app-shell"
import { PageHeader } from "@/components/page-header"
import { Badge } from "@/components/ui/badge"
import { ApiError, fetchAgentRuns } from "@/lib/api"
import { MODULE_LABELS, runSummaryText } from "@/lib/admin-utils"
import { moduleVerdictBadgeClass, moduleVerdictLabel } from "@/lib/badge-utils"
import type { AgentRunSummary, ModuleName } from "@/lib/admin-types"

const FILTERS: { value: ModuleName | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "support", label: "Support Inbox" },
  { value: "extraction", label: "Document Extraction" },
  { value: "meeting", label: "Meeting Notes" },
  { value: "chat", label: "Ask a Question" },
]

export default function AdminPage() {
  const [filter, setFilter] = React.useState<ModuleName | "all">("all")
  const [runs, setRuns] = React.useState<AgentRunSummary[] | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    setRuns(null)
    fetchAgentRuns(filter === "all" ? undefined : filter)
      .then(setRuns)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load agent runs."))
  }, [filter])

  return (
    <AppShell>
      <div className="h-full overflow-y-auto">
        <PageHeader
          icon={ScrollText}
          eyebrow="Unified activity feed"
          title="Agent runs"
          description="Every automation run across all four modules, with the first-pass draft and the checker's verdict."
        />

        <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 pb-8 sm:px-6">
          <div className="flex flex-wrap gap-1.5">
            {FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter(f.value)}
                className={
                  "rounded-full border px-3 py-1 text-xs transition-colors " +
                  (filter === f.value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:text-foreground")
                }
              >
                {f.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {!runs && !error && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Loading agent runs...
            </div>
          )}

          {runs && runs.length === 0 && (
            <p className="text-sm text-muted-foreground">No agent runs yet for this filter.</p>
          )}

          {runs && runs.length > 0 && (
            <div className="stagger grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {runs.map((run) => (
                <Link
                  key={run.id}
                  href={`/admin/${run.id}`}
                  className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary/40"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{MODULE_LABELS[run.module]}</Badge>
                    {run.verdict && (
                      <Badge className={moduleVerdictBadgeClass(run.module, run.verdict)}>
                        {moduleVerdictLabel(run.module, run.verdict)}
                      </Badge>
                    )}
                  </div>
                  <p className="line-clamp-2 text-sm text-foreground">{runSummaryText(run.module, run.input)}</p>
                  <span className="mt-auto text-xs text-muted-foreground">
                    {new Date(run.created_at).toLocaleString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}
