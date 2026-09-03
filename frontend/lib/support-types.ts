export type SupportDraft = {
  category: string
  draft_reply: string
}

export type CheckerVerdict = {
  verdict: "approved" | "rejected"
  citation: string
  critique: string
  corrected_category: string
}

export type SupportResult = {
  draft: SupportDraft
  checker: CheckerVerdict
  final: SupportDraft
  citations: string[]
}
