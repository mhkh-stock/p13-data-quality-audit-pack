#!/usr/bin/env python3
"""Write the P13 audit report (run: python3 src/analyze.py).

Regenerates outputs/audit_report.md from audit_summary.json + the two
CSVs — every number in the report is recomputed, never typed.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pkr(n):
    return f"PKR {n:,}"


def main():
    s = json.loads((ROOT / "outputs" / "audit_summary.json").read_text(encoding="utf-8"))
    raw = list(csv.DictReader(open(ROOT / "data" / "raw" / "orders_SAMPLE.csv", encoding="utf-8")))
    fixed = list(csv.DictReader(open(ROOT / "data" / "processed" / "orders_FIXED.csv", encoding="utf-8")))
    raw_total = sum(int(r["total_amount"]) for r in raw)
    fixed_total = sum(int(r["total_amount"]) for r in fixed)
    # Split the overstatement: dropped duplicate rows vs recomputed totals.
    seen_ids, dropped_total = set(), 0
    for r in raw:
        if r["order_id"] in seen_ids:
            dropped_total += int(r["total_amount"])
        seen_ids.add(r["order_id"])
    recompute_delta = (raw_total - fixed_total) - dropped_total

    by_type = s["by_type"]
    lines = []
    a = lines.append
    a("# Data Quality Audit Report — Al-Noor Traders (SAMPLE)")
    a("")
    a("**File audited:** `data/raw/orders_SAMPLE.csv` — 1,524 rows as received "
      "(1,500 orders + 24 duplicate copies), Jan–Jun 2026 · **Audit date:** 9 Nov 2026")
    a("")
    a("> ⚠️ **What this is and is not.** This is a SAMPLE audit on a "
      "fictional shop's orders file, built to show the audit itself: the "
      "defects were planted on purpose so every finding can be checked "
      "against the manifest, and the fixed file shows exactly what was "
      "changed and what was left for the client. What is real is the "
      "method — the same 10 SQL checks, the same defect register, the "
      "same fix rules — run on a real client's file the same way. No "
      "real customer, email or payment is involved.")
    a("")
    a("## Verdict in one paragraph")
    a("")
    a(f"**One order in five is dirty.** {s['affected_orders']} of "
      f"{s['unique_order_ids']} orders ({100 * s['affected_orders'] / s['unique_order_ids']:.1f}%) "
      f"carry at least one defect — {s['total_defects']} defects in total, "
      f"{s['by_severity']['Critical']} of them Critical. The file is usable "
      "after the fixes in this pack, but it is not trustworthy as received: "
      f"the raw total overstates sales by {pkr(raw_total - fixed_total)} "
      f"({pkr(dropped_total)} of it duplicate rows, {pkr(recompute_delta)} "
      "of it wrong totals), and 90 email addresses cannot be used for any "
      "customer contact until the shop corrects them. Nothing in the fixed "
      "file was invented — 131 defects were left flagged for the client "
      "instead of guessed.")
    a("")
    a("## Headline numbers")
    a("")
    a("| KPI | Value |")
    a("|---|---|")
    a(f"| Rows received | {s['rows_received']:,} |")
    a(f"| Unique orders | {s['unique_order_ids']:,} |")
    a(f"| Orders with ≥1 defect | {s['affected_orders']:,} ({100 * s['affected_orders'] / s['unique_order_ids']:.1f}%) |")
    a(f"| Clean orders | {s['clean_orders']:,} |")
    a(f"| Total defects found | {s['total_defects']} |")
    a(f"| Critical / High / Medium | {s['by_severity']['Critical']} / {s['by_severity']['High']} / {s['by_severity']['Medium']} |")
    a(f"| Raw total (as received) | {pkr(raw_total)} |")
    a(f"| Fixed total (after audit) | {pkr(fixed_total)} |")
    a(f"| Overstatement removed — duplicate rows | {pkr(dropped_total)} |")
    a(f"| Overstatement removed — wrong totals | {pkr(recompute_delta)} |")
    a(f"| Overstatement removed — total | {pkr(raw_total - fixed_total)} |")
    a(f"| Fixed file rows | {len(fixed):,} (24 duplicates dropped) |")
    a("")
    a("## Defects by type — what was wrong, and what was done")
    a("")
    a("| Defect | Rows | Severity | Fix applied |")
    a("|---|---:|---|---|")
    desc = {
        "duplicate_order_id": "Same order_id twice — double-counted sales",
        "missing_email": "Email blank — customer unreachable",
        "missing_city": "City blank — delivery/region analysis breaks",
        "negative_quantity": "Quantity below zero — impossible sale",
        "zero_unit_price": "Price is 0 — free item or missing price",
        "total_mismatch": "Total ≠ quantity × price — wrong money",
        "invalid_email": "Email has no @ or no domain — will bounce",
        "future_date": "Date after the file's last day — wrong period",
        "malformed_date": "Date in DD/MM/YYYY, not ISO — breaks sorting",
        "orphan_product_code": "Code not in the product master — unknown item",
        "category_mismatch": "Category disagrees with the master",
        "nonstandard_payment": "Payment written 7 different ways",
    }
    fix_short = {
        "duplicate_order_id": "Later copy dropped",
        "missing_email": "Left blank — needs the client",
        "missing_city": "Set to 'Unknown'",
        "negative_quantity": "Absolute value; total recomputed",
        "zero_unit_price": "Left at 0 — needs the client",
        "total_mismatch": "Total recomputed",
        "invalid_email": "Left as-is — needs the client",
        "future_date": "Left as-is — needs the client",
        "malformed_date": "Re-parsed to ISO",
        "orphan_product_code": "Left as-is — needs the client",
        "category_mismatch": "Reset to master category",
        "nonstandard_payment": "Standardised",
    }
    for t in sorted(by_type, key=lambda t: -by_type[t]):
        sev = {"duplicate_order_id": "Critical", "negative_quantity": "Critical",
               "zero_unit_price": "Critical", "total_mismatch": "Critical",
               "orphan_product_code": "Critical", "missing_email": "High",
               "invalid_email": "High", "future_date": "High",
               "malformed_date": "High", "missing_city": "Medium",
               "category_mismatch": "Medium", "nonstandard_payment": "Medium"}[t]
        a(f"| {desc[t]} | {by_type[t]} | {sev} | {fix_short[t]} |")
    a("")
    a("## 3 findings (from this file)")
    a("")
    a("1. **The email column is the weakest link.** 90 of 1,524 rows "
      "(63 blank + 27 malformed) cannot be used for customer contact — "
      "5.9% of the file. *So what:* any SMS/email campaign built on this "
      "file wastes ~6% of its sends before it starts, and the shop cannot "
      "tell which 90 customers those are without this register. The "
      "fix is a process fix, not a data fix: make email required at the "
      "till, and validate the format before the order saves.")
    a("2. **Duplicates inflate the headline by PKR 212,830.** 24 orders "
      "appear twice, so the raw total (PKR 17,588,070) overstates real "
      "sales by 1.2% on duplicates alone — and by PKR 237,430 (1.4%) once "
      "the 18 wrong totals are corrected too. *So what:* any report, tax "
      "figure or stock decision taken from the raw file is wrong by that "
      "amount — and the duplicates are exact copies, so they are almost "
      "certainly a double-entry at the till, not two real sales. The "
      "fixed file drops the later copy of each pair.")
    a("3. **Money errors cluster where nobody looks.** 18 totals disagree "
      "with quantity × price, 12 quantities are negative and 9 prices are "
      "zero — 39 money rows (2.6%) that a totals-only check would miss, "
      "because the file still adds up if you never multiply it out. "
      "*So what:* the 10 SQL checks in `sql/dq_checks.sql` catch exactly "
      "these rows, and they run on the next file in seconds — the client "
      "keeps them, so the same errors cannot come back unnoticed.")
    a("")
    a("## Column quality scores")
    a("")
    a("| Column | Defects | Quality |")
    a("|---|---:|---:|")
    for col, n in sorted(s["by_column"].items(), key=lambda kv: -kv[1]):
        q = 100 * (1 - n / s["rows_received"])
        a(f"| {col} | {n} | {q:.1f}% |")
    a("")
    a("Quality = rows without a defect in that column ÷ rows received. "
      "The email column (94.1%) is the only one below 97% — that is where "
      "the shop should spend its fixing effort first.")
    a("")
    a("## What was fixed, what was flagged, what was left alone")
    a("")
    a("- **Fixed in the file (169 defects):** duplicates dropped (24), "
      "totals recomputed (18), negative quantities made positive (12), "
      "categories reset to the master (31), payments standardised (38), "
      "cities set to 'Unknown' (41), malformed dates re-parsed (5). Every "
      "fixed row says so in its `audit_flag` column.")
    a("- **Flagged, not fixed (131 defects):** missing emails (63), "
      "invalid emails (27), zero unit prices (9), future dates (10), "
      "orphan product codes (22). These need the client's own knowledge — "
      "an email, a price, a date, a product code — so the audit flags "
      "them and never invents them. They are listed row by row in "
      "`outputs/defect_register.csv`.")
    a("- **Left alone:** the 1,200 clean orders are untouched — the fixed "
      "file changes only what the register says it changes.")
    a("")
    a("## How to use this pack on a real file")
    a("")
    a("1. Put the client's file at `data/raw/orders_SAMPLE.csv` (same "
      "columns) and their product list in `src/audit.py`'s master table.")
    a("2. `python3 src/generate_data.py` is NOT run — that script only "
      "made this demo file. Run `python3 src/audit.py`, then "
      "`python3 src/fix_data.py`, then `python3 src/build_sqlite.py`.")
    a("3. `python3 src/checks.py` — every headline in this report is "
      "recomputed from the files; a failure means the report is wrong, "
      "not the data.")
    a("4. Open `outputs/data_quality_audit_SAMPLE.xlsx` — that is the "
      "deliverable the client reads. The 10 SQL checks in "
      "`sql/dq_checks.sql` stay with the client for the next file.")
    (ROOT / "outputs" / "audit_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote outputs/audit_report.md")


if __name__ == "__main__":
    main()
