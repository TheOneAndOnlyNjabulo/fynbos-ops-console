"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  ClipboardList,
  FileText,
  Inbox,
  LayoutDashboard,
  Leaf,
  MessageCircleQuestion,
} from "lucide-react"

import { ThemeToggle } from "@/components/theme-toggle"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/support", label: "Support Inbox", icon: Inbox },
  { href: "/extract", label: "Document Extraction", icon: FileText },
  { href: "/meeting-notes", label: "Meeting Notes", icon: ClipboardList },
  { href: "/chat", label: "Ask a Question", icon: MessageCircleQuestion },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="flex h-svh flex-col">
      {/* Top bar - single unified header across every breakpoint, no sidebar / no bottom tabs */}
      <header className="shrink-0 border-b border-border/70 bg-background/95 backdrop-blur">
        <div className="flex items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link href="/" className="flex items-center gap-2">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Leaf className="size-4.5" strokeWidth={1.75} aria-hidden="true" />
            </span>
            <div className="leading-tight">
              <div className="text-sm font-bold tracking-tight">Fynbos Retail</div>
              <div className="text-[10px] text-muted-foreground">Ops Console</div>
            </div>
          </Link>
          <div className="flex items-center gap-2">
            <span className="hidden text-[11px] text-muted-foreground sm:inline">Internal tool</span>
            <ThemeToggle />
          </div>
        </div>

        <nav className="flex gap-1 overflow-x-auto border-t border-border/50 px-3 py-1.5 sm:px-5">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="size-4" strokeWidth={1.75} aria-hidden="true" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </header>

      {/* Main content - a bounded viewport; each page owns its own scroll region within it */}
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  )
}
