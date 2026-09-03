"use client"

import * as React from "react"
import { AlertTriangle, CheckCircle2, Calculator, FileText, Loader2, Upload } from "lucide-react"

import { PageHeader } from "@/components/page-header"
import { Timeline, TimelineStep } from "@/components/stage-timeline"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ApiError, submitInvoice } from "@/lib/api"
import { validationBadgeClass, validationLabel } from "@/lib/badge-utils"
import type { ExtractResult } from "@/lib/extraction-types"

export function ExtractionForm() {
  const [file, setFile] = React.useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = React.useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [result, setResult] = React.useState<ExtractResult | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const canSubmit = file !== null && !isSubmitting

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null
    setFile(selected)
    setResult(null)
    setError(null)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null)
  }

  async function handleSubmit() {
    if (!canSubmit || !file) return

    setIsSubmitting(true)
    setError(null)
    setResult(null)

    try {
      const run = await submitInvoice(file)
      setResult(run)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        icon={FileText}
        eyebrow="Extract + Validation Agent"
        title="Document Extraction"
        description="Upload a supplier invoice (PNG, JPEG, or WEBP). It's extracted automatically, then independently checked for arithmetic and routed to the right approval level per policy."
      />

      <div className="flex flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden">
      {/* Section 1: invoice upload */}
      <div className="shrink-0 border-b border-border/70 p-6 md:w-[24rem] md:overflow-y-auto md:border-r md:border-b-0">
        <div className="flex flex-col gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handleFileChange}
            className="hidden"
            aria-label="Upload invoice"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border p-6 text-center transition-colors hover:border-primary/50"
          >
            {previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={previewUrl} alt="Invoice preview" className="max-h-40 rounded-md border border-border" />
            ) : (
              <>
                <Upload className="size-6 text-muted-foreground" strokeWidth={1.5} aria-hidden="true" />
                <span className="text-sm text-muted-foreground">Click to choose an invoice image</span>
              </>
            )}
            {file && <span className="text-xs text-muted-foreground">{file.name}</span>}
          </button>

          <Button onClick={handleSubmit} disabled={!canSubmit} className="self-end">
            {isSubmitting ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Extracting...
              </>
            ) : (
              <>
                <FileText className="size-4" /> Process invoice
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

      {/* Section 2: extraction + validation results */}
      <div className="flex-1 p-6 md:overflow-y-auto">
        {!result && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <FileText className="size-8" strokeWidth={1.5} aria-hidden="true" />
            <p className="max-w-xs text-sm">
              The Extraction Agent&apos;s fields, the arithmetic check, and the Validation Agent&apos;s routing
              decision will appear here once you process an invoice.
            </p>
          </div>
        )}

        {result && (
          <div className="mx-auto max-w-2xl">
            <Timeline>
            <TimelineStep index={1} title="Extraction Agent">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                <dt className="text-muted-foreground">Vendor</dt>
                <dd>{result.extraction.vendor_name}</dd>
                <dt className="text-muted-foreground">Invoice #</dt>
                <dd>{result.extraction.invoice_number}</dd>
                <dt className="text-muted-foreground">Date</dt>
                <dd>{result.extraction.invoice_date}</dd>
                <dt className="text-muted-foreground">PO number</dt>
                <dd>{result.extraction.po_number || <span className="italic text-muted-foreground">none</span>}</dd>
              </dl>

              <div className="mt-2 overflow-hidden rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-xs text-muted-foreground">
                    <tr>
                      <th className="px-2 py-1.5 text-left font-medium">Description</th>
                      <th className="px-2 py-1.5 text-right font-medium">Qty</th>
                      <th className="px-2 py-1.5 text-right font-medium">Unit price</th>
                      <th className="px-2 py-1.5 text-right font-medium">Line total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.extraction.line_items.map((li, i) => (
                      <tr key={i} className="border-t border-border/70">
                        <td className="px-2 py-1.5">{li.description}</td>
                        <td className="px-2 py-1.5 text-right">{li.quantity}</td>
                        <td className="px-2 py-1.5 text-right">R{li.unit_price.toFixed(2)}</td>
                        <td className="px-2 py-1.5 text-right">R{li.line_total.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-end gap-6 text-sm">
                <div className="flex flex-col items-end">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>R{result.extraction.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex flex-col items-end">
                  <span className="text-muted-foreground">VAT</span>
                  <span>R{result.extraction.vat_amount.toFixed(2)}</span>
                </div>
                <div className="flex flex-col items-end font-semibold">
                  <span className="text-muted-foreground font-normal">Grand total</span>
                  <span>R{result.extraction.grand_total.toFixed(2)}</span>
                </div>
              </div>
            </TimelineStep>

            <TimelineStep
              index={2}
              icon={result.arithmetic.has_discrepancy ? AlertTriangle : Calculator}
              tone={result.arithmetic.has_discrepancy ? "negative" : "default"}
              title="Arithmetic check (deterministic)"
            >
              <div className="flex items-center gap-2 text-sm">
                {result.arithmetic.has_discrepancy && (
                  <AlertTriangle className="size-4 shrink-0 text-destructive" aria-hidden="true" />
                )}
                <span>{result.arithmetic.description}</span>
              </div>
            </TimelineStep>

            <TimelineStep
              index={3}
              icon={result.validation.verdict === "auto_approved" ? CheckCircle2 : undefined}
              tone={result.validation.verdict === "auto_approved" ? "positive" : "default"}
              title="Validation Agent — routing decision"
              last
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge className={validationBadgeClass(result.validation.verdict)}>
                  {validationLabel(result.validation.verdict)}
                </Badge>
                <span className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
                  {result.validation.citation}
                </span>
              </div>
              {result.validation.issues.length > 0 && (
                <ul className="list-disc pl-5 text-sm text-foreground">
                  {result.validation.issues.map((issue, i) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              )}
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
