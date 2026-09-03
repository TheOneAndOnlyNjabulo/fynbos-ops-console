export type LineItem = {
  description: string
  quantity: number
  unit_price: number
  line_total: number
}

export type Extraction = {
  vendor_name: string
  invoice_number: string
  invoice_date: string
  po_number: string
  line_items: LineItem[]
  subtotal: number
  vat_amount: number
  grand_total: number
}

export type ArithmeticCheck = {
  has_discrepancy: boolean
  description: string
}

export type Validation = {
  verdict: "auto_approved" | "needs_manager_approval" | "needs_finance_director_approval" | "flagged"
  citation: string
  issues: string[]
}

export type ExtractResult = {
  extraction: Extraction
  arithmetic: ArithmeticCheck
  validation: Validation
  citations: string[]
}
