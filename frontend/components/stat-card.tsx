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
    <div className="flex items-center gap-4 rounded-3xl bg-card px-5 py-4">
      <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-background text-foreground">
        <Icon className="size-5" strokeWidth={2} aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <div className="text-xs font-semibold text-muted-foreground">{label}</div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-2xl font-extrabold tracking-tight">{value}</span>
          {hint && <span className="truncate text-xs text-muted-foreground">{hint}</span>}
        </div>
      </div>
    </div>
  )
}
