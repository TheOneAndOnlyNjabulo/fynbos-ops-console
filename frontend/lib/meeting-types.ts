export type ActionItem = {
  task: string
  owner: string
  due_date: string
}

export type GroundingResult = {
  task: string
  grounded: boolean
  supporting_quote: string
  reason: string
}

export type MeetingNotesResult = {
  summary: string
  all_action_items: ActionItem[]
  grounding_results: GroundingResult[]
  final_action_items: ActionItem[]
  citations: string[]
}
