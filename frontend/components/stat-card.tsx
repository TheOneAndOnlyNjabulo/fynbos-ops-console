import type { LucideIcon } from "lucide-react"

export function StatCard({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: LucideIcon
  label: string
  value: string
  hint?: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3.5">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-primary/25 bg-primary/10 text-primary">
        <Icon className="size-4" strokeWidth={1.75} aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <div className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">{label}</div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-lg font-bold tracking-tight">{value}</span>
          {hint && <span className="truncate text-xs text-muted-foreground">{hint}</span>}
        </div>
      </div>
    </div>
  )
}
