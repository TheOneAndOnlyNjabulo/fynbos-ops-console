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
    accent: "support" as const,
    icon: Inbox,
    tag: "Draft + Policy Checker",
    title: "Support Inbox",
    description: "Draft a reply to a customer email, then independently check it against policy.",
  },
  {
    href: "/extract",
    accent: "extract" as const,
    icon: FileText,
    tag: "Extract + Validation Agent",
    title: "Document Extraction",
    description: "Pull structured fields from a supplier invoice and route it for approval.",
  },
  {
    href: "/meeting-notes",
    accent: "meeting" as const,
    icon: ClipboardList,
    tag: "Extract + Grounding Checker",
    title: "Meeting Notes",
    description: "Turn a transcript into action items, each one verified against the transcript.",
  },
  {
    href: "/chat",
    accent: "ask" as const,
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
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-4 pt-8 pb-10 sm:px-6">
          {/* Hero: oversized type on the white canvas, no container */}
          <section className="flex animate-rise flex-wrap items-end justify-between gap-6">
            <div className="max-w-2xl">
              <span className="inline-block rounded-full bg-muted px-3 py-1 text-xs font-semibold text-muted-foreground">
                Fictional South African online retailer
              </span>
              <h1 className="mt-4 text-4xl leading-[1.05] font-extrabold tracking-tight sm:text-6xl">
                Four agent workflows.
                <br />
                <span className="text-muted-foreground">One ops console.</span>
              </h1>
              <p className="mt-4 max-w-lg text-base leading-relaxed text-muted-foreground">
                Each workflow pairs a drafting agent with an independent checker before anything is accepted,
                and every run lands in one activity log.
              </p>
            </div>
            <Link
              href="/admin"
              className="inline-flex h-12 items-center gap-2 rounded-full bg-primary px-6 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-85"
            >
              Activity log <ArrowRight className="size-4" />
            </Link>
          </section>

          {/* Bento: the first workflow is featured, the rest fill around it */}
          <section className="stagger grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:grid-rows-2">
            {MODULES.map((m, index) => (
              <ModuleCard
                key={m.href}
                {...m}
                featured={index === 0}
                className={
                  index === 0
                    ? "sm:col-span-2 lg:row-span-2"
                    : index === 1
                      ? "lg:col-span-2"
                      : undefined
                }
              />
            ))}
          </section>

          <section className="stagger grid gap-4 sm:grid-cols-3">
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
          </section>

          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-extrabold tracking-tight">Recent activity</h2>
              <Link
                href="/admin"
                className="flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-semibold hover:bg-muted"
              >
                View all <ArrowRight className="size-4" />
              </Link>
            </div>

            {error && (
              <div className="rounded-3xl bg-destructive/10 px-5 py-4 text-sm text-destructive">{error}</div>
            )}

            {!runs && !error && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" /> Loading recent activity...
              </div>
            )}

            {runs && runs.length === 0 && (
              <p className="text-sm text-muted-foreground">No agent runs yet. Try one of the workflows above.</p>
            )}

            {runs && runs.length > 0 && (
              <div className="stagger flex flex-col gap-2">
                {runs.slice(0, 6).map((run) => (
                  <Link
                    key={run.id}
                    href={`/admin/${run.id}`}
                    className="flex items-center justify-between gap-3 rounded-2xl bg-card px-5 py-3.5 transition-colors hover:bg-accent"
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
                      <p className="mt-1.5 truncate text-sm font-medium text-foreground">
                        {runSummaryText(run.module, run.input)}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs font-medium text-muted-foreground">
                      {new Date(run.created_at).toLocaleDateString()}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  )
}
