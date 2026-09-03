"use client"

import * as React from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Loader2 } from "lucide-react"

import { AppShell } from "@/components/app-shell"
import { Card, CardContent, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ApiError, fetchAgentRun } from "@/lib/api"
import { MODULE_LABELS } from "@/lib/admin-utils"
import { moduleVerdictBadgeClass, moduleVerdictLabel } from "@/lib/badge-utils"
import type { AgentRunDetail } from "@/lib/admin-types"

type LineItem = { description: string; quantity: number; unit_price: number; line_total: number }
type ActionItem = { task: string; owner: string; due_date: string }

export default function AdminRunDetailPage() {
  const params = useParams<{ id: string }>()
  const [run, setRun] = React.useState<AgentRunDetail | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    fetchAgentRun(params.id)
      .then(setRun)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load agent run."))
  }, [params.id])

  return (
    <AppShell>
      <div className="h-full overflow-y-auto">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-6 py-8">
          <Link
            href="/admin"
            className="flex w-fit items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-3.5" /> All agent runs
          </Link>

          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {!run && !error && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Loading agent run...
            </div>
          )}

          {run && (
            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{MODULE_LABELS[run.module]}</Badge>
                {run.verdict && (
                  <Badge className={moduleVerdictBadgeClass(run.module, run.verdict)}>
                    {moduleVerdictLabel(run.module, run.verdict)}
                  </Badge>
                )}
                <span className="text-xs text-muted-foreground">{new Date(run.created_at).toLocaleString()}</span>
              </div>

              <RunBody run={run} />

              {run.critique && (
                <StageCard title="Critique">
                  <p className="text-sm leading-relaxed">{run.critique}</p>
                </StageCard>
              )}

              {run.citations.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {run.citations.map((citation) => (
                    <span
                      key={citation}
                      className="rounded-full border border-border bg-muted px-2 py-0.5 font-mono text-[10px] text-muted-foreground"
                    >
                      {citation}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}

function RunBody({ run }: { run: AgentRunDetail }) {
  switch (run.module) {
    case "support":
      return <SupportBody run={run} />
    case "extraction":
      return <ExtractionBody run={run} />
    case "meeting":
      return <MeetingBody run={run} />
    case "chat":
      return <ChatBody run={run} />
    default:
      return null
  }
}

function SupportBody({ run }: { run: AgentRunDetail }) {
  const draft = run.draft as { category: string; draft_reply: string } | null
  const final = run.final as { category: string; draft_reply: string } | null
  return (
    <>
      <StageCard title="Original email">
        <p className="text-sm leading-relaxed">{String(run.input.email_text ?? "")}</p>
      </StageCard>
      {draft && (
        <StageCard title="Draft Agent — first pass">
          <Badge variant="outline">{draft.category}</Badge>
          <p className="text-sm leading-relaxed">{draft.draft_reply}</p>
        </StageCard>
      )}
      {final && (
        <StageCard title="Final reply">
          <Badge variant="outline">{final.category}</Badge>
          <p className="text-sm leading-relaxed">{final.draft_reply}</p>
        </StageCard>
      )}
    </>
  )
}

function ExtractionBody({ run }: { run: AgentRunDetail }) {
  const extraction = run.final as
    | {
        vendor_name: string
        invoice_number: string
        invoice_date: string
        po_number: string
        line_items: LineItem[]
        subtotal: number
        vat_amount: number
        grand_total: number
      }
    | null
  if (!extraction) return null
  return (
    <StageCard title="Extracted invoice">
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <dt className="text-muted-foreground">Vendor</dt>
        <dd>{extraction.vendor_name}</dd>
        <dt className="text-muted-foreground">Invoice #</dt>
        <dd>{extraction.invoice_number}</dd>
        <dt className="text-muted-foreground">PO number</dt>
        <dd>{extraction.po_number || <span className="italic text-muted-foreground">none</span>}</dd>
        <dt className="text-muted-foreground">Grand total</dt>
        <dd>R{extraction.grand_total?.toFixed(2)}</dd>
      </dl>
      <ul className="text-sm text-muted-foreground">
        {extraction.line_items?.map((li, i) => (
          <li key={i}>
            {li.description} — R{li.line_total?.toFixed(2)}
          </li>
        ))}
      </ul>
    </StageCard>
  )
}

function MeetingBody({ run }: { run: AgentRunDetail }) {
  const final = run.final as { summary: string; action_items: ActionItem[] } | null
  if (!final) return null
  return (
    <>
      <StageCard title="Summary">
        <p className="text-sm leading-relaxed">{final.summary}</p>
      </StageCard>
      <StageCard title="Verified action items">
        {final.action_items.length === 0 && (
          <p className="text-sm text-muted-foreground">None verified.</p>
        )}
        <ul className="flex flex-col gap-1 text-sm">
          {final.action_items.map((item, i) => (
            <li key={i}>
              {item.task}
              {item.owner && <span className="text-muted-foreground"> — {item.owner}</span>}
              {item.due_date && <span className="text-muted-foreground"> (due {item.due_date})</span>}
            </li>
          ))}
        </ul>
      </StageCard>
    </>
  )
}

function ChatBody({ run }: { run: AgentRunDetail }) {
  const final = run.final as { answer: string } | null
  return (
    <>
      <StageCard title="Question">
        <p className="text-sm leading-relaxed">{String(run.input.question ?? "")}</p>
      </StageCard>
      {final && (
        <StageCard title="Answer">
          <p className="text-sm leading-relaxed">{final.answer}</p>
        </StageCard>
      )}
    </>
  )
}

function StageCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="gap-2 p-4">
      <CardTitle>{title}</CardTitle>
      <CardContent className="gap-2 p-0">{children}</CardContent>
    </Card>
  )
}
