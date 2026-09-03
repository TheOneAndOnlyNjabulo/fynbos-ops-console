# Evaluation Results

Generated: 2026-09-03T12:26:01+00:00

## Summary

- **Support Inbox**: 8/8 correctly classified (final category)
- **Document Extraction**: 4/4 fully correct (vendor + PO + routing)
- **Meeting Notes**: 3/3 correct (expected items kept, no over-extraction)

## Support Inbox

| # | Email | Expected | Final | Auditor | Passed |
|---|---|---|---|---|---|
| 1 | I want to return these shoes, they just don't f... | Returns & Refunds | Returns & Refunds | rejected | yes |
| 2 | My blender arrived with a cracked lid, can you ... | Damaged/Defective Item | Damaged/Defective Item | rejected | yes |
| 3 | I found this exact TV cheaper on another site, ... | Price Match | Price Match | rejected | yes |
| 4 | My card was charged twice for the same order, p... | Payment & Billing | Payment & Billing | rejected | yes |
| 5 | How many loyalty points do I have and when do t... | Loyalty & Rewards | Loyalty & Rewards | approved | yes |
| 6 | I have a question about how your gift cards work. | Gift Cards & Vouchers | Gift Cards & Vouchers | approved | yes |
| 7 | The TV I bought three months ago just stopped t... | Warranty | Warranty | rejected | yes |
| 8 | Can I cancel my order? I haven't received a dis... | Cancellation | Cancellation | rejected | yes |

## Document Extraction

| # | Fixture | Vendor OK | PO OK | Verdict | Expected | Passed |
|---|---|---|---|---|---|---|
| 1 | clean_small.png | yes | yes | auto_approved | auto_approved | yes |
| 2 | clean_large.png | yes | yes | needs_finance_director_approval | needs_finance_director_approval | yes |
| 3 | missing_po.png | yes | yes | flagged | flagged | yes |
| 4 | bad_arithmetic.png | yes | yes | flagged | flagged | yes |

## Meeting Notes

| # | Expected items present | Item count ≤ bound | Final tasks | Passed |
|---|---|---|---|---|
| 1 | yes | yes (1/1) | Pull together the Q3 returns numbers | yes |
| 2 | yes | yes (1/1) | Confirm whether the gift card display bug is a caching issue | yes |
| 3 | yes | yes (2/2) | Follow up with the packaging supplier to get an explanation for the delays; Double check that the Silver and Gold loyalty thresholds are correct in the system | yes |
