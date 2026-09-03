"use client"

import * as React from "react"
import Link from "next/link"
import {
  ArrowRight,
  ClipboardList,
  FileText,
  Inbox,
  LayoutDashboard,
  ListChecks,
  Loader2,
  MessageCircleQuestion,
  ShieldCheck,
} from "lucide-react"

import { AppShell } from "@/components/app-shell"
import { PageHeader } from "@/components/page-header"
import { ModuleCard } from "@/components/module-card"
import { StatCard } from "@/components/stat-card"
import { Badge } from "@/components/ui/badge"
import { ApiError, fetchAgentRuns } from "@/lib/api"
import { MODULE_LABELS, runSummaryText } from "@/lib/admin-utils"
import { moduleVerdictBadgeClass, moduleVerdictLabel } from "@/lib/badge-utils"
import type { AgentRunSummary } from "@/lib/admin-types"

const MODULES = [
  {
    href: "/support",
    icon: Inbox,
    tag: "Draft + Policy Checker",
    title: "Support Inbox",
    description: "Draft a reply to a customer email, then independently check it against policy.",
  },
  {
    href: "/extract",
    icon: FileText,
    tag: "Extract + Validation Agent",
    title: "Document Extraction",
    description: "Pull structured fields from a supplier invoice and route it for approval.",
  },
  {
    href: "/meeting-notes",
    icon: ClipboardList,
    tag: "Extract + Grounding Checker",
    title: "Meeting Notes",
    description: "Turn a transcript into action items, each one verified against the transcript.",
  },
  {
    href: "/chat",
    icon: MessageCircleQuestion,
    tag: "Retrieval-augmented",
    title: "Ask a Question",
    description: "Ask general staff questions, answered and cited from the policy corpus.",
  },
]

function isRejectedLike(verdict: string | null): boolean {
  if (!verdict) return false
  if (verdict === "rejected" || verdict === "flagged") return true
  if (verdict.startsWith("needs_")) return true
  const match = verdict.match(/^(\d+)\/(\d+)/)
  if (match) return match[1] !== match[2]
  return false
}

export default function DashboardPage() {
  const [runs, setRuns] = React.useState<AgentRunSummary[] | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    fetchAgentRuns()
      .then(setRuns)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load recent activity."))
  }, [])

  const flaggedCount = runs?.filter((r) => isRejectedLike(r.verdict)).length ?? 0
  const activeModules = new Set(runs?.map((r) => r.module)).size

  return (
    <AppShell>
      <div className="h-full overflow-y-auto">
        <PageHeader
          icon={LayoutDashboard}
          eyebrow="Overview"
          title="Ops Console"
          description="Four agent workflows and one activity log for Fynbos Retail, a fictional South African online retailer."
        />

        <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-8">
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard
              icon={ListChecks}
              label="Logged runs"
              value={runs ? String(runs.length) : "—"}
              hint="most recent"
            />
            <StatCard
              icon={ShieldCheck}
              label="Checker caught"
              value={runs ? String(flaggedCount) : "—"}
              hint="rejected / flagged / routed"
            />
            <StatCard
              icon={LayoutDashboard}
              label="Modules active"
              value={runs ? String(activeModules) : "—"}
              hint="of 4"
            />
          </div>

          <div>
            <h2 className="mb-3 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              Workflows
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {MODULES.map((m) => (
                <ModuleCard key={m.href} {...m} />
              ))}
            </div>
          </div>

          <div>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                Recent activity
              </h2>
              <Link
                href="/admin"
                className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                View all <ArrowRight className="size-3" />
              </Link>
            </div>

            {error && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}

            {!runs && !error && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Loading recent activity...
              </div>
            )}

            {runs && runs.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No agent runs yet. Try one of the workflows above.
              </p>
            )}

            {runs && runs.length > 0 && (
              <div className="flex flex-col divide-y divide-border/70 rounded-xl border border-border bg-card">
                {runs.slice(0, 6).map((run) => (
                  <Link
                    key={run.id}
                    href={`/admin/${run.id}`}
                    className="flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-muted/50"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{MODULE_LABELS[run.module]}</Badge>
                        {run.verdict && (
                          <Badge className={moduleVerdictBadgeClass(run.module, run.verdict)}>
                            {moduleVerdictLabel(run.module, run.verdict)}
                          </Badge>
                        )}
                      </div>
                      <p className="mt-1 truncate text-sm text-foreground">
                        {runSummaryText(run.module, run.input)}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {new Date(run.created_at).toLocaleDateString()}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
