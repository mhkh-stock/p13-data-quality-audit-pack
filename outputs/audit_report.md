# Data Quality Audit Report — Al-Noor Traders (SAMPLE)

**File audited:** `data/raw/orders_SAMPLE.csv` — 1,524 rows as received (1,500 orders + 24 duplicate copies), Jan–Jun 2026 · **Audit date:** 9 Nov 2026

> ⚠️ **What this is and is not.** This is a SAMPLE audit on a fictional shop's orders file, built to show the audit itself: the defects were planted on purpose so every finding can be checked against the manifest, and the fixed file shows exactly what was changed and what was left for the client. What is real is the method — the same 10 SQL checks, the same defect register, the same fix rules — run on a real client's file the same way. No real customer, email or payment is involved.

## Verdict in one paragraph

**One order in five is dirty.** 300 of 1500 orders (20.0%) carry at least one defect — 300 defects in total, 85 of them Critical. The file is usable after the fixes in this pack, but it is not trustworthy as received: the raw total overstates sales by PKR 237,430 (PKR 212,830 of it duplicate rows, PKR 24,600 of it wrong totals), and 90 email addresses cannot be used for any customer contact until the shop corrects them. Nothing in the fixed file was invented — 131 defects were left flagged for the client instead of guessed.

## Headline numbers

| KPI | Value |
|---|---|
| Rows received | 1,524 |
| Unique orders | 1,500 |
| Orders with ≥1 defect | 300 (20.0%) |
| Clean orders | 1,200 |
| Total defects found | 300 |
| Critical / High / Medium | 85 / 105 / 110 |
| Raw total (as received) | PKR 17,588,070 |
| Fixed total (after audit) | PKR 17,350,640 |
| Overstatement removed — duplicate rows | PKR 212,830 |
| Overstatement removed — wrong totals | PKR 24,600 |
| Overstatement removed — total | PKR 237,430 |
| Fixed file rows | 1,500 (24 duplicates dropped) |

## Defects by type — what was wrong, and what was done

| Defect | Rows | Severity | Fix applied |
|---|---:|---|---|
| Email blank — customer unreachable | 63 | High | Left blank — needs the client |
| City blank — delivery/region analysis breaks | 41 | Medium | Set to 'Unknown' |
| Payment written 7 different ways | 38 | Medium | Standardised |
| Category disagrees with the master | 31 | Medium | Reset to master category |
| Email has no @ or no domain — will bounce | 27 | High | Left as-is — needs the client |
| Same order_id twice — double-counted sales | 24 | Critical | Later copy dropped |
| Code not in the product master — unknown item | 22 | Critical | Left as-is — needs the client |
| Total ≠ quantity × price — wrong money | 18 | Critical | Total recomputed |
| Quantity below zero — impossible sale | 12 | Critical | Absolute value; total recomputed |
| Date after the file's last day — wrong period | 10 | High | Left as-is — needs the client |
| Price is 0 — free item or missing price | 9 | Critical | Left at 0 — needs the client |
| Date in DD/MM/YYYY, not ISO — breaks sorting | 5 | High | Re-parsed to ISO |

## 3 findings (from this file)

1. **The email column is the weakest link.** 90 of 1,524 rows (63 blank + 27 malformed) cannot be used for customer contact — 5.9% of the file. *So what:* any SMS/email campaign built on this file wastes ~6% of its sends before it starts, and the shop cannot tell which 90 customers those are without this register. The fix is a process fix, not a data fix: make email required at the till, and validate the format before the order saves.
2. **Duplicates inflate the headline by PKR 212,830.** 24 orders appear twice, so the raw total (PKR 17,588,070) overstates real sales by 1.2% on duplicates alone — and by PKR 237,430 (1.4%) once the 18 wrong totals are corrected too. *So what:* any report, tax figure or stock decision taken from the raw file is wrong by that amount — and the duplicates are exact copies, so they are almost certainly a double-entry at the till, not two real sales. The fixed file drops the later copy of each pair.
3. **Money errors cluster where nobody looks.** 18 totals disagree with quantity × price, 12 quantities are negative and 9 prices are zero — 39 money rows (2.6%) that a totals-only check would miss, because the file still adds up if you never multiply it out. *So what:* the 10 SQL checks in `sql/dq_checks.sql` catch exactly these rows, and they run on the next file in seconds — the client keeps them, so the same errors cannot come back unnoticed.

## Column quality scores

| Column | Defects | Quality |
|---|---:|---:|
| customer_email | 90 | 94.1% |
| city | 41 | 97.3% |
| payment_method | 38 | 97.5% |
| category | 31 | 98.0% |
| order_id | 24 | 98.4% |
| product_code | 22 | 98.6% |
| total_amount | 18 | 98.8% |
| order_date | 15 | 99.0% |
| quantity | 12 | 99.2% |
| unit_price | 9 | 99.4% |

Quality = rows without a defect in that column ÷ rows received. The email column (94.1%) is the only one below 97% — that is where the shop should spend its fixing effort first.

## What was fixed, what was flagged, what was left alone

- **Fixed in the file (169 defects):** duplicates dropped (24), totals recomputed (18), negative quantities made positive (12), categories reset to the master (31), payments standardised (38), cities set to 'Unknown' (41), malformed dates re-parsed (5). Every fixed row says so in its `audit_flag` column.
- **Flagged, not fixed (131 defects):** missing emails (63), invalid emails (27), zero unit prices (9), future dates (10), orphan product codes (22). These need the client's own knowledge — an email, a price, a date, a product code — so the audit flags them and never invents them. They are listed row by row in `outputs/defect_register.csv`.
- **Left alone:** the 1,200 clean orders are untouched — the fixed file changes only what the register says it changes.

## How to use this pack on a real file

1. Put the client's file at `data/raw/orders_SAMPLE.csv` (same columns) and their product list in `src/audit.py`'s master table.
2. `python3 src/generate_data.py` is NOT run — that script only made this demo file. Run `python3 src/audit.py`, then `python3 src/fix_data.py`, then `python3 src/build_sqlite.py`.
3. `python3 src/checks.py` — every headline in this report is recomputed from the files; a failure means the report is wrong, not the data.
4. Open `outputs/data_quality_audit_SAMPLE.xlsx` — that is the deliverable the client reads. The 10 SQL checks in `sql/dq_checks.sql` stay with the client for the next file.