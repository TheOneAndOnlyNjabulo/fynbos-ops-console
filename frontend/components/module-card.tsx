import Link from "next/link"
import type { LucideIcon } from "lucide-react"
import { ArrowUpRight } from "lucide-react"

export function ModuleCard({
  href,
  icon: Icon,
  title,
  description,
  tag,
}: {
  href: string
  icon: LucideIcon
  title: string
  description: string
  tag: string
}) {
  return (
    <Link
      href={href}
      className="group relative flex flex-col gap-3 overflow-hidden rounded-xl border border-border bg-card p-5 transition-colors hover:border-primary/40"
    >
      <div
        className="pointer-events-none absolute -top-10 -right-10 size-32 rounded-full bg-primary/[0.06] transition-transform duration-300 group-hover:scale-125"
        aria-hidden="true"
      />
      <div className="flex items-start justify-between">
        <div className="flex size-9 items-center justify-center rounded-lg border border-primary/25 bg-primary/10 text-primary">
          <Icon className="size-4.5" strokeWidth={1.75} aria-hidden="true" />
        </div>
        <ArrowUpRight
          className="size-4 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary"
          aria-hidden="true"
        />
      </div>
      <div>
        <div className="text-[10px] font-semibold tracking-wide text-muted-foreground uppercase">{tag}</div>
        <div className="font-semibold tracking-tight">{title}</div>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
    </Link>
  )
}
