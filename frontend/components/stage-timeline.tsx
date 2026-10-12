import type { LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"

/**
 * A vertical connected-step visual for showing a draft -> check -> final
 * agent pipeline, used by Support Inbox, Document Extraction, and Meeting
 * Notes. Each module's stages have different content, so this only owns the
 * numbered node + connecting line chrome - callers render whatever's inside.
 */
export function Timeline({ children }: { children: React.ReactNode }) {
  return <div className="stagger flex flex-col">{children}</div>
}

export function TimelineStep({
  index,
  icon: Icon,
  title,
  tone = "default",
  last = false,
  children,
}: {
  index: number
  icon?: LucideIcon
  title: string
  tone?: "default" | "positive" | "negative"
  last?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div
          className={cn(
            "flex size-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
            tone === "positive" && "border-emerald-600/30 bg-emerald-600/10 text-emerald-600",
            tone === "negative" && "border-destructive/30 bg-destructive/10 text-destructive",
            tone === "default" && "border-primary/25 bg-primary/10 text-primary"
          )}
        >
          {Icon ? <Icon className="size-3.5" strokeWidth={2} aria-hidden="true" /> : index}
        </div>
        {!last && <div className="my-1 w-px flex-1 bg-border" />}
      </div>
      <div className={cn("flex flex-col gap-2", last ? "pb-0" : "pb-6")}>
        <h2 className="pt-0.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h2>
        {children}
      </div>
    </div>
  )
}
