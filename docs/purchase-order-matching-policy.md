# Purchase Order Matching Policy

## 1. Three-way match

Every invoice is matched against three records before payment: the original purchase order (what was ordered),
the goods receipt note (what was actually received), and the invoice itself (what is being billed). Payment is
not released unless all three agree.

## 2. Quantity tolerance

A quantity variance of up to 2% between the purchase order and the goods receipt note is accepted automatically
(accounting for normal handling variance on bulk orders). Anything beyond 2% is flagged for manual review.

## 3. Price tolerance

A unit price variance of up to 1% between the purchase order and the invoice is accepted automatically, to allow
for minor rounding. A variance beyond 1% is flagged, since it may indicate an unauthorized price change.

## 4. Partial deliveries

An invoice for a partial delivery (fewer units than the original PO) is matched against the goods receipt note
for that partial quantity only, not the full PO quantity - the remaining balance stays open against the same PO
for a future invoice.

## 5. Unmatched invoices

An invoice that cannot be matched to any open purchase order is not paid and is returned to the supplier with a
request to confirm the correct PO reference, rather than being approved on the assumption that the goods were
genuinely ordered.
