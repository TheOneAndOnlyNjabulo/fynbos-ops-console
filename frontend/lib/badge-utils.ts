export function verdictBadgeClass(verdict: string | null) {
  return verdict === "approved" ? "bg-emerald-600 text-white" : "bg-destructive text-destructive-foreground"
}
