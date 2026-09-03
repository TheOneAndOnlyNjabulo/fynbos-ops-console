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
