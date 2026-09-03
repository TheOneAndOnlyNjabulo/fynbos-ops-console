import type { LucideIcon } from "lucide-react"

export function PageHeader({
  icon: Icon,
  eyebrow,
  title,
  description,
  action,
}: {
  icon: LucideIcon
  eyebrow: string
  title: string
  description: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border/70 px-6 py-6">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg border border-primary/25 bg-primary/10 text-primary">
          <Icon className="size-4.5" strokeWidth={1.75} aria-hidden="true" />
        </div>
        <div>
          <div className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">{eyebrow}</div>
          <h1 className="text-xl font-bold tracking-tight">{title}</h1>
          <p className="mt-0.5 max-w-lg text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
