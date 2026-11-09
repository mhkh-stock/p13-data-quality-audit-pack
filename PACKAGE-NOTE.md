# PACKAGE NOTE — P13: Data Quality Audit Pack

**Fiverr-ready gig title:** "I will audit your dataset and deliver a fixed file plus the checks to keep it clean"

## What the buyer gets

A full audit, not a one-off clean-up: a defect register (every defect
found, by row, column and severity), a fixed file (duplicates dropped,
totals recomputed, categories and payments standardised — with an
`audit_flag` column saying exactly what changed on every row), an
Excel audit workbook whose KPIs are live formulas, and 10 SQL checks
the buyer keeps and runs on their next file. Delivered on this
sample: 1,524 rows audited, 300 defects found (85 Critical), PKR
237,430 of overstatement removed, 66 data-quality checks passing.

## Tiers

| Tier | Price | Delivery | Includes |
|---|---|---|---|
| **Basic — $20** | $20 | 2 days | Audit of one dataset (up to 5,000 rows) → defect register (CSV) + audit report with the 3 key findings. |
| **Standard — $65** | $65 | 4 days | Everything in Basic + fixed file (duplicates dropped, totals recomputed, values standardised, every change flagged) + Excel audit workbook with live-formula KPIs, by-type table and column quality scores + the 10 SQL checks to keep. |
| **Premium — $140** | $140 | 7 days | Everything in Standard + audit of a second file in the same run + a monthly re-audit setup (same checks, dated snapshots, change report like a P4 tracker) + a 30-min walkthrough call on the findings and the process fixes that stop the defects coming back. |

## What the buyer must provide

- The dataset (CSV or Excel, up to 5,000 rows Basic / 20,000 Standard
  / 50,000 Premium), and the columns that must be unique, must not be
  blank, or must match a reference list.
- Any reference lists the audit should check against (product master,
  customer list, price list) — without them, orphan/lookup checks
  cannot run.
- The date window the file is supposed to cover, and which money
  columns must reconcile (e.g. total = quantity × price).

## Notes for the seller (Hashir)

- Sample built on a fictional shop's generated file with 300 defects
  planted on purpose — the audit re-finds all 300 without reading the
  manifest, which is the proof to show a buyer. Never present the demo
  Al-Noor Traders file as a real client audit; the deliverable is the
  method, the sample proves it.
- The audit never invents data: missing emails, zero prices, future
  dates and orphan codes are flagged, not guessed. Say this to the
  buyer up front — it is the trust line that separates an audit from a
  silent clean-up.
- For a real order, confirm in writing which columns are keys, which
  must not be blank, and which reference lists apply — then the same
  scripts run on their file with only the master table swapped.
- Monthly re-audit (Premium) reuses the P4 snapshot-diff pattern:
  same audit, dated snapshots, defect-count change report.
