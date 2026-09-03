"use client"

import * as React from "react"
import { CheckCircle2, FileEdit, Inbox, Loader2, Send, XCircle } from "lucide-react"

import { PageHeader } from "@/components/page-header"
import { Timeline, TimelineStep } from "@/components/stage-timeline"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ApiError, submitSupportEmail } from "@/lib/api"
import { verdictBadgeClass } from "@/lib/badge-utils"
import type { SupportResult } from "@/lib/support-types"

export function SupportForm() {
  const [emailText, setEmailText] = React.useState("")
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [result, setResult] = React.useState<SupportResult | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  const canSubmit = emailText.trim().length > 0 && !isSubmitting

  async function handleSubmit() {
    if (!canSubmit) return

    setIsSubmitting(true)
    setError(null)
    setResult(null)

    try {
      const run = await submitSupportEmail(emailText.trim())
      setResult(run)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const wasRevised = result !== null && result.checker.verdict === "rejected"

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        icon={Inbox}
        eyebrow="Draft + Policy Checker"
        title="Support Inbox"
        description="Paste a customer email. It's drafted automatically, then independently checked against Fynbos's policy documents before the reply is finalized."
      />

      <div className="flex flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden">
      {/* Section 1: email intake */}
      <div className="shrink-0 border-b border-border/70 p-6 md:w-[24rem] md:overflow-y-auto md:border-r md:border-b-0">
        <div className="flex flex-col gap-3">
          <Textarea
            value={emailText}
            onChange={(event) => setEmailText(event.target.value)}
            placeholder="e.g. My blender arrived with a cracked lid, can you help?"
            rows={6}
            disabled={isSubmitting}
            aria-label="Customer email"
          />
          <Button onClick={handleSubmit} disabled={!canSubmit} className="self-end">
            {isSubmitting ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Processing...
              </>
            ) : (
              <>
                <Send className="size-4" /> Process email
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

      {/* Section 2: live audit trail */}
      <div className="flex-1 p-6 md:overflow-y-auto">
        {!result && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <Inbox className="size-8" strokeWidth={1.5} aria-hidden="true" />
            <p className="max-w-xs text-sm">
              The Draft Agent&apos;s reply, the Policy Checker&apos;s verdict, and the final result will appear
              here once you process an email.
            </p>
          </div>
        )}

        {result && (
          <div className="mx-auto max-w-2xl">
            <Timeline>
              <TimelineStep index={1} title="Draft Agent — first pass">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{result.draft.category}</Badge>
                </div>
                <p className="text-sm leading-relaxed">{result.draft.draft_reply}</p>
              </TimelineStep>

              <TimelineStep
                index={2}
                icon={result.checker.verdict === "approved" ? CheckCircle2 : XCircle}
                tone={result.checker.verdict === "approved" ? "positive" : "negative"}
                title="Policy Checker — independent check"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className={verdictBadgeClass(result.checker.verdict)}>
                    {result.checker.verdict === "approved" ? "Approved" : "Rejected"}
                  </Badge>
                  <span className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
                    {result.checker.citation}
                  </span>
                </div>
                {result.checker.verdict === "rejected" && (
                  <p className="text-sm leading-relaxed text-foreground">{result.checker.critique}</p>
                )}
              </TimelineStep>

              <TimelineStep
                index={3}
                icon={wasRevised ? FileEdit : undefined}
                title={wasRevised ? "Final reply — corrected" : "Final reply"}
                last
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{result.final.category}</Badge>
                </div>
                <p className="text-sm leading-relaxed">{result.final.draft_reply}</p>
                {result.citations.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
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
              </TimelineStep>
            </Timeline>
          </div>
        )}
      </div>
      </div>
    </div>
  )
}
