/**
 * Small pieces shared by the module forms so a visitor has something useful to
 * do while the demo backend wakes up: sample inputs to try, and a short
 * explanation of the pipeline their request is about to go through.
 */

export function SamplePicker({
  samples,
  onPick,
  disabled = false,
}: {
  samples: { label: string; value: string }[]
  onPick: (value: string) => void
  disabled?: boolean
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      <span className="self-center text-xs text-muted-foreground">
        Try a sample:
      </span>
      {samples.map((sample) => (
        <button
          key={sample.label}
          type="button"
          onClick={() => onPick(sample.value)}
          disabled={disabled}
          className="rounded-full border border-border bg-card px-3 py-1 text-xs text-foreground/80 transition-colors hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
        >
          {sample.label}
        </button>
      ))}
    </div>
  )
}

/**
 * A static explainer, not live progress - the backend returns one response at the
 * end, so animating these steps would imply status it doesn't actually report.
 */
export function HowItWorks({ steps }: { steps: string[] }) {
  return (
    <div className="mt-4 max-w-sm rounded-xl border border-border bg-card p-4 text-left">
      <h2 className="text-xs font-semibold tracking-wide text-foreground uppercase">
        How it works
      </h2>
      <ol className="mt-2 flex list-decimal flex-col gap-1.5 pl-4 text-xs leading-relaxed">
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
    </div>
  )
}
