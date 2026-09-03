"use client"

import * as React from "react"
import { CheckCircle2, ClipboardList, Loader2, Send, XCircle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ApiError, submitTranscript } from "@/lib/api"
import type { MeetingNotesResult } from "@/lib/meeting-types"

export function MeetingForm() {
  const [transcript, setTranscript] = React.useState("")
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [result, setResult] = React.useState<MeetingNotesResult | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  const canSubmit = transcript.trim().length > 0 && !isSubmitting

  async function handleSubmit() {
    if (!canSubmit) return

    setIsSubmitting(true)
    setError(null)
    setResult(null)

    try {
      const run = await submitTranscript(transcript.trim())
      setResult(run)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto md:flex-row md:overflow-hidden">
      {/* Section 1: transcript intake */}
      <div className="shrink-0 border-b border-border/70 p-6 md:w-[26rem] md:overflow-y-auto md:border-r md:border-b-0">
        <h1 className="text-2xl font-bold tracking-tight">Meeting Notes</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Paste a meeting transcript. Action items are extracted automatically, then each one is independently
          verified against the transcript before it&apos;s kept.
        </p>

        <div className="mt-6 flex flex-col gap-3">
          <Textarea
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            placeholder="e.g. Priya: Sipho, can you pull the Q3 numbers by Friday? Sipho: Sure..."
            rows={12}
            disabled={isSubmitting}
            aria-label="Meeting transcript"
          />
          <Button onClick={handleSubmit} disabled={!canSubmit} className="self-end">
            {isSubmitting ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Processing...
              </>
            ) : (
              <>
                <Send className="size-4" /> Process transcript
              </>
            )}
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}
      </div>

      {/* Section 2: summary + per-item grounding results */}
      <div className="flex-1 p-6 md:overflow-y-auto">
        {!result && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <ClipboardList className="size-8" strokeWidth={1.5} aria-hidden="true" />
            <p className="max-w-xs text-sm">
              The summary and each action item&apos;s grounding verdict will appear here once you process a
              transcript.
            </p>
          </div>
        )}

        {result && (
          <div className="mx-auto flex max-w-2xl flex-col gap-4">
            <StageCard title="1. Extraction Agent — summary">
              <p className="text-sm leading-relaxed">{result.summary}</p>
            </StageCard>

            <StageCard
              title={`2. Grounding Checker — ${result.final_action_items.length}/${result.all_action_items.length} action items verified`}
            >
              {result.all_action_items.length === 0 && (
                <p className="text-sm text-muted-foreground">No action items were identified in this transcript.</p>
              )}
              <div className="flex flex-col gap-2">
                {result.grounding_results.map((r, i) => {
                  const item = result.all_action_items[i]
                  return (
                    <div
                      key={i}
                      className="flex flex-col gap-1 rounded-lg border border-border/70 p-3 text-sm"
                    >
                      <div className="flex items-start gap-2">
                        {r.grounded ? (
                          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-500" aria-hidden="true" />
                        ) : (
                          <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" aria-hidden="true" />
                        )}
                        <div className="flex flex-col gap-1">
                          <span className={r.grounded ? "" : "text-muted-foreground line-through"}>
                            {item.task}
                          </span>
                          {(item.owner || item.due_date) && (
                            <div className="flex gap-1.5">
                              {item.owner && <Badge variant="outline">{item.owner}</Badge>}
                              {item.due_date && <Badge variant="outline">{item.due_date}</Badge>}
                            </div>
                          )}
                          {r.grounded ? (
                            <span className="font-mono text-[11px] text-muted-foreground">
                              &ldquo;{r.supporting_quote}&rdquo;
                            </span>
                          ) : (
                            <span className="text-[11px] text-destructive">{r.reason}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </StageCard>

            {result.citations.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {result.citations.map((citation) => (
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
  )
}

function StageCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
      <h2 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h2>
      {children}
    </div>
  )
}
