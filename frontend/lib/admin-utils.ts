import type { ModuleName } from "@/lib/admin-types"

export const MODULE_LABELS: Record<ModuleName, string> = {
  support: "Support Inbox",
  extraction: "Document Extraction",
  meeting: "Meeting Notes",
  chat: "Ask a Question",
}

export function runSummaryText(module: ModuleName, input: Record<string, unknown>): string {
  switch (module) {
    case "support":
      return String(input.email_text ?? "")
    case "extraction":
      return String(input.filename ?? "")
    case "meeting":
      return String(input.transcript ?? "")
    case "chat":
      return String(input.question ?? "")
    default:
      return ""
  }
}
