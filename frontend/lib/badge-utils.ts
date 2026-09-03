export function verdictBadgeClass(verdict: string | null) {
  return verdict === "approved" ? "bg-emerald-600 text-white" : "bg-destructive text-destructive-foreground"
}

export function validationBadgeClass(verdict: string) {
  switch (verdict) {
    case "auto_approved":
      return "bg-emerald-600 text-white"
    case "needs_manager_approval":
      return "bg-amber-500 text-white"
    case "needs_finance_director_approval":
      return "bg-amber-600 text-white"
    default:
      return "bg-destructive text-destructive-foreground"
  }
}

export function validationLabel(verdict: string) {
  switch (verdict) {
    case "auto_approved":
      return "Auto-approved"
    case "needs_manager_approval":
      return "Needs manager approval"
    case "needs_finance_director_approval":
      return "Needs finance director approval"
    default:
      return "Flagged for review"
  }
}

/** Meeting Notes stores a free-text "N/M action items grounded" verdict rather than
 * a fixed enum - parse it to decide green (nothing dropped) vs amber (some dropped). */
export function meetingVerdictBadgeClass(verdict: string) {
  const match = verdict.match(/^(\d+)\/(\d+)/)
  if (!match) return "bg-secondary text-secondary-foreground"
  const [, grounded, total] = match
  return grounded === total ? "bg-emerald-600 text-white" : "bg-amber-500 text-white"
}

/** Dispatches to the right badge-color function per module, since each module's
 * verdict field means something different (approve/reject, a 4-state routing
 * decision, or a free-text fraction) - see meeting_agent.py's module docstring
 * for why these three shapes exist rather than one shared verdict type. */
export function moduleVerdictBadgeClass(module: string, verdict: string) {
  switch (module) {
    case "support":
      return verdictBadgeClass(verdict)
    case "extraction":
      return validationBadgeClass(verdict)
    case "meeting":
      return meetingVerdictBadgeClass(verdict)
    default:
      return "bg-secondary text-secondary-foreground"
  }
}

export function moduleVerdictLabel(module: string, verdict: string) {
  switch (module) {
    case "support":
      return verdict === "approved" ? "Approved" : "Rejected"
    case "extraction":
      return validationLabel(verdict)
    default:
      return verdict
  }
}
