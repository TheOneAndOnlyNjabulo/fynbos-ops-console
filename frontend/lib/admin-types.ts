export type ModuleName = "support" | "extraction" | "meeting" | "chat"

export type AgentRunSummary = {
  id: string
  module: ModuleName
  input: Record<string, unknown>
  verdict: string | null
  created_at: string
}

export type AgentRunDetail = {
  id: string
  module: ModuleName
  input: Record<string, unknown>
  draft: Record<string, unknown> | null
  verdict: string | null
  critique: string | null
  final: Record<string, unknown> | null
  citations: string[]
  created_at: string
}
