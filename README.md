# P13 — Data Quality Audit Pack: 1,524 rows in, a trustworthy file out

**Client (SAMPLE):** Al-Noor Traders, Lahore — general store orders,
Jan–Jun 2026 · **Audited:** 9 Nov 2026 · **Status: SAMPLE delivery on DEMO data**
**Tools:** Python (pandas-free stdlib audit) · SQL (10 checks) · SQLite · Excel (live formulas + native chart)
**Deliverable:** `outputs/data_quality_audit_SAMPLE.xlsx`
(Audit Summary + Defect Register + Fixed Data, 1,500 orders)

> ⚠️ **What this is and is not.** The orders file is a fictional
> shop's demo data with 300 defects planted on purpose, so every
> finding in this pack can be checked against the manifest — the audit
> re-finds all 300 without reading it. No real customer, email or
> payment is involved. What is real is the method: the same 10 SQL
> checks, the same defect register, the same fix rules run on a real
> client's file the same way, and the fixed file shows exactly what
> was changed and what was left for the client instead of guessed.

## Business question it answers

> "Is my data trustworthy — and what exactly is wrong with it?"

A shop that reports, taxes or orders stock from a dirty file makes
wrong decisions with confidence. This delivery audits the file
(defect by defect, with severity), fixes what can be fixed honestly,
flags what needs the client's own knowledge, and leaves the client
with 10 SQL checks that catch the same errors on the next file.

## What is inside

| File | What it does |
|---|---|
| `outputs/data_quality_audit_SAMPLE.xlsx` | The deliverable: Audit Summary (10 KPIs + defects-by-type table + column scores, all live formulas) + Defect Register (300 rows) + Fixed Data (1,500 rows) + native bar chart |
| `outputs/audit_report.md` | Findings report: verdict, headline numbers, defects by type, 3 findings with "so what", column scores, fixed-vs-flagged split |
| `outputs/defect_register.csv` | One row per defect: DQ-0001…DQ-0300, order, column, type, severity, detail, fix applied |
| `outputs/audit_summary.json` | Machine-readable audit summary (counts by type / severity / column) |
| `data/raw/orders_SAMPLE.csv` | The file as received: 1,524 rows with 300 planted defects |
| `data/raw/defect_manifest.json` | The planted-defect manifest the audit is checked against |
| `data/processed/orders_FIXED.csv` | The fixed file: 1,500 rows + `audit_flag` column (276 flagged, 1,224 OK) |
| `data/processed/orders.db` | SQLite: raw_orders + fixed_orders + product_master + defect_register (NOT uploaded — rebuildable) |
| `data/README.md` | Data dictionary + known quirks |
| `sql/schema.sql` | Star-lite schema for the four tables |
| `sql/dq_checks.sql` | The 10 SQL checks the client keeps — each returns 0 rows on a clean file |
| `src/generate_data.py` | Makes the demo file (seeded; NOT run on a real client file) |
| `src/audit.py` | The audit: detects all 12 defect types from the data itself |
| `src/fix_data.py` | Applies the documented fixes, flags the rest |
| `src/build_sqlite.py` | Loads raw + fixed + master + register into SQLite |
| `src/analyze.py` | Regenerates the report — every number recomputed, never typed |
| `src/build_workbook.py` | Builds the workbook: 3 sheets, live formulas, native chart |
| `src/checks.py` | Data-quality checks as code — 66 checks, all passing |
| `requirements.txt` | Pinned: `openpyxl==3.1.2` (Python 3.12; the audit itself is stdlib-only) |

## How it fits together

```
client's orders file ──▶ src/audit.py ──▶ outputs/defect_register.csv + audit_summary.json
        (1,524 rows)              │                    │
                                  ▼                    ▼
                          src/fix_data.py ──▶ data/processed/orders_FIXED.csv
                                  │                    │
                                  ▼                    ▼
                          src/build_sqlite.py ──▶ data/processed/orders.db
                                  │              (NOT uploaded: rebuildable)
                                  ▼
                          src/analyze.py ──▶ outputs/audit_report.md
                                  │
                                  ▼
                          src/build_workbook.py ──▶ outputs/data_quality_audit_SAMPLE.xlsx
                                  ▲ src/checks.py verifies all of it (66 checks)
```

## 3 key findings (from this file)

1. **One order in five is dirty.** 300 of 1,500 orders (20.0%) carry
   at least one defect — 300 defects, 85 of them Critical. *So what:*
   the file is usable after this pack's fixes, but no report, tax
   figure or stock decision should ever be taken from the raw file.
2. **Duplicates inflate the headline by PKR 212,830.** 24 orders
   appear twice (exact copies — almost certainly double-entry at the
   till), and 18 wrong totals add another PKR 24,600. The raw total
   overstates sales by PKR 237,430 (1.4%). *So what:* the fixed file
   drops the later copy of each pair and recomputes every total.
3. **The email column is the weakest link.** 90 of 1,524 rows (63
   blank + 27 malformed) cannot be used for customer contact — 5.9%
   of the file, and the only column below 97% quality. *So what:* the
   fix is a process fix — make email required at the till and validate
   the format before the order saves — not a data fix.

## Verified numbers

| KPI | Value |
|---|---|
| Rows received / unique orders | 1,524 / 1,500 |
| Orders with ≥1 defect / clean orders | 300 (20.0%) / 1,200 |
| Total defects found | 300 (85 Critical / 105 High / 110 Medium) |
| Defect types | 12 (each count matches the planted manifest exactly) |
| Raw total / fixed total (PKR) | 17,588,070 / 17,350,640 |
| Overstatement removed (PKR) | 237,430 (212,830 duplicates + 24,600 wrong totals) |
| Fixed file | 1,500 rows, 276 flagged, 1,224 OK |
| Fixed, not guessed | 169 defects fixed · 131 flagged for the client |
| SQL checks the client keeps | 10, each returning exactly the planted count on the raw file |
| Checks | 66 passing (`python3 src/checks.py`) |

Verification: `python3 src/checks.py` (66 checks pass — file shape,
audit-vs-manifest exact match on all 12 defect types, money
reconciliation to the rupee, fixed-file integrity, all 10 SQL checks
returning exactly the planted counts, workbook structure, and every
headline number in the report) **and** the workbook was opened in
LibreOffice, which calculated every formula: Summary shows 1,524 rows
received, 300 affected orders, 1,224 clean, PKR 17,350,640 fixed
total, 276 rows still flagged, by-type table totalling 300 with
shares summing to 100% — identical to the Python recompute.

## Limits — what this delivery does not do

- **Demo data, one file, one day.** A real client's file has its own
  columns, its own master list and its own defect mix — the audit
  scripts take the client's master and column names as inputs (see
  "How to use it on a real file" in the report), but the defect list
  here is the 12 types this sample was built to show.
- **131 defects are flagged, not fixed.** Missing/invalid emails (90),
  zero prices (9), future dates (10) and orphan product codes (22)
  need the client's own knowledge. The audit never invents an email, a
  price, a date or a product — a "fixed" file that guesses those is
  worse than a flagged one.
- **One defect per order in this sample.** The planting kept defect
  types on disjoint rows so each count could be verified exactly; a
  real file will have rows with several defects at once, and the
  register handles that (one row per defect, not per order).
- **Open it in Excel or Google Sheets to see the numbers.** The
  workbook carries live formulas (openpyxl writes formulas, not cached
  values), so they calculate when the file is opened — a raw file
  reader that does not calculate formulas will show blanks instead of
  KPI values.

## How to run it (under 5 steps)

First time only: `pip install -r requirements.txt` (only openpyxl;
the audit itself is Python stdlib).

1. `python3 src/generate_data.py` — makes the demo file (skip this on
   a real client file; put theirs at `data/raw/orders_SAMPLE.csv`).
2. `python3 src/audit.py` — detects the defects → defect register +
   summary.
3. `python3 src/fix_data.py` — applies the fixes → fixed file.
4. `python3 src/build_sqlite.py` — loads everything into SQLite.
5. `python3 src/analyze.py` — regenerates the report.
6. `python3 src/build_workbook.py` — rebuilds the workbook.
7. `python3 src/checks.py` — 66 checks, all must pass.
8. Open `outputs/data_quality_audit_SAMPLE.xlsx` — that is the deliverable.
9. To reuse it for a real client: put their file + product master in
   place of the demo ones and re-run steps 2–7 — the register, the
   report and the workbook rebuild themselves from the new rows, and
   the 10 SQL checks in `sql/dq_checks.sql` stay with the client for
   the next file.

## Tools

- Python 3.12 (stdlib audit; openpyxl 3.1.2 for the workbook)
- SQLite (star-lite schema) · Excel / Google Sheets (the client's tool)

## Data source note

**SAMPLE data, generated 9 Nov 2026 for this audit** (seeded Python
generator, fictional shop "Al-Noor Traders"). No real customer, email
or payment is involved. The audit, the SQL checks, the fixed file and
the workbook are the product; the numbers exist to prove them.

## Repo standard note

This paid project follows the portfolio repo standard (Master Plan
§3.2): README + data dictionary (`data/README.md`) + the deliverable
workbook + reproducible scripts + a Fiverr-ready package note
(`PACKAGE-NOTE.md`). The workbook is the deliverable a buyer opens;
the scripts are the proof it was built, not typed.
