// Each workflow owns one flat accent colour (defined in globals.css), used for its
// dashboard tile, page header mark, and "how it works" block. Class names are
// spelled out in full so Tailwind can see them at build time.
export type ModuleAccent = "support" | "extract" | "meeting" | "ask"

export const ACCENT_BG: Record<ModuleAccent, string> = {
  support: "bg-support",
  extract: "bg-extract",
  meeting: "bg-meeting",
  ask: "bg-ask",
}
