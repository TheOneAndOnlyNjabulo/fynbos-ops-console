import Link from "next/link"
import type { LucideIcon } from "lucide-react"
import { ArrowUpRight } from "lucide-react"

import { ACCENT_BG, type ModuleAccent } from "@/lib/module-theme"
import { cn } from "@/lib/utils"

/**
 * A flat, solid-colour dashboard tile. The decoration is two plain geometric
 * shapes rather than an illustration - it adds rhythm across the grid without
 * any gradient, shadow, or texture.
 */
export function ModuleCard({
  href,
  icon: Icon,
  title,
  description,
  tag,
  accent,
  featured = false,
  className,
}: {
  href: string
  icon: LucideIcon
  title: string
  description: string
  tag: string
  accent: ModuleAccent
  featured?: boolean
  className?: string
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group relative flex flex-col justify-between gap-8 overflow-hidden rounded-3xl p-6 text-on-accent transition-transform duration-200 hover:-translate-y-0.5 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none",
        ACCENT_BG[accent],
        featured && "min-h-72",
        className
      )}
    >
      <div
        className={cn(
          "pointer-events-none absolute rounded-full bg-on-accent/10 transition-transform duration-500 group-hover:scale-110",
          featured ? "-right-16 -bottom-16 size-72" : "-right-10 -bottom-12 size-40"
        )}
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute top-6 right-20 size-6 rounded-full bg-white/60"
        aria-hidden="true"
      />

      <div className="relative flex items-start justify-between">
        <div className="flex size-11 items-center justify-center rounded-2xl bg-on-accent text-white">
          <Icon className="size-5" strokeWidth={2} aria-hidden="true" />
        </div>
        <span className="flex size-10 items-center justify-center rounded-full bg-white/70 transition-transform group-hover:rotate-45">
          <ArrowUpRight className="size-4" strokeWidth={2.25} aria-hidden="true" />
        </span>
      </div>

      <div className="relative">
        <span className="inline-block rounded-full bg-on-accent/10 px-2.5 py-0.5 text-[11px] font-bold tracking-wide uppercase">
          {tag}
        </span>
        <div
          className={cn(
            "mt-2 font-extrabold tracking-tight",
            featured ? "text-3xl sm:text-4xl" : "text-xl"
          )}
        >
          {title}
        </div>
        <p className={cn("mt-1.5 text-sm leading-relaxed text-on-accent/75", featured && "max-w-xs sm:text-base")}>
          {description}
        </p>
      </div>
    </Link>
  )
}
