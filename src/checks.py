#!/usr/bin/env python3
"""Data-quality checks as code for P13 (run: python3 src/checks.py).

Every check recomputes from the CSVs / DB / workbook independently —
nothing trusts a number typed in the README. Exit code 0 = all pass.
"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
MANIFEST = ROOT / "data" / "raw" / "defect_manifest.json"
FIXED = ROOT / "data" / "processed" / "orders_FIXED.csv"
DB = ROOT / "data" / "processed" / "orders.db"
REG = ROOT / "outputs" / "defect_register.csv"
SUMMARY = ROOT / "outputs" / "audit_summary.json"
REPORT = ROOT / "outputs" / "audit_report.md"
XLSX = ROOT / "outputs" / "data_quality_audit_SAMPLE.xlsx"

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def main():
    raw = list(csv.DictReader(open(RAW, encoding="utf-8")))
    fixed = list(csv.DictReader(open(FIXED, encoding="utf-8")))
    reg = list(csv.DictReader(open(REG, encoding="utf-8")))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    report = REPORT.read_text(encoding="utf-8")

    print("== file shape ==")
    check("1,524 rows received (1,500 + 24 duplicates)", len(raw) == 1524, f"got {len(raw)}")
    check("1,500 unique order_ids", len({r["order_id"] for r in raw}) == 1500)
    check("fixed file has 1,500 rows", len(fixed) == 1500)
    check("fixed order_ids unique", len({r["order_id"] for r in fixed}) == 1500)
    check("fixed file keeps every original order_id",
          {r["order_id"] for r in fixed} == {r["order_id"] for r in raw})

    print("== audit vs manifest ==")
    check("audit found exactly 300 defects", len(reg) == 300, f"got {len(reg)}")
    from collections import Counter
    by_type = Counter(d["defect_type"] for d in reg)
    for dtype, info in manifest["defects"].items():
        check(f"audit found {info['count']} x {dtype}",
              by_type[dtype] == info["count"], f"got {by_type[dtype]}")
    check("300 distinct orders affected",
          len({d["order_id"] for d in reg}) == 300)
    check("defect_ids DQ-0001..DQ-0300 unique",
          len({d["defect_id"] for d in reg}) == 300
          and {d["defect_id"] for d in reg} == {f"DQ-{i:04d}" for i in range(1, 301)})
    check("severities sum to 300 (85 Critical / 105 High / 110 Medium)",
          Counter(d["severity"] for d in reg) == {"Critical": 85, "High": 105, "Medium": 110},
          str(Counter(d["severity"] for d in reg)))
    check("summary JSON matches the register",
          summary["total_defects"] == 300 and summary["affected_orders"] == 300
          and summary["clean_orders"] == 1200)

    print("== money reconciliation ==")
    raw_total = sum(int(r["total_amount"]) for r in raw)
    fixed_total = sum(int(r["total_amount"]) for r in fixed)
    check("raw total PKR 17,588,070", raw_total == 17588070, f"got {raw_total}")
    check("fixed total PKR 17,350,640", fixed_total == 17350640, f"got {fixed_total}")
    check("overstatement PKR 237,430", raw_total - fixed_total == 237430)
    seen, dropped_total = set(), 0
    for r in raw:
        if r["order_id"] in seen:
            dropped_total += int(r["total_amount"])
        seen.add(r["order_id"])
    check("duplicate rows account for PKR 212,830", dropped_total == 212830, f"got {dropped_total}")
    check("wrong totals account for PKR 24,600",
          (raw_total - fixed_total) - dropped_total == 24600)

    print("== fixed file integrity ==")
    check("every fixed row totals quantity x price",
          all(int(r["total_amount"]) == int(r["quantity"]) * int(r["unit_price"])
              for r in fixed))
    check("no negative quantities in fixed file",
          all(int(r["quantity"]) > 0 for r in fixed))
    check("no duplicate order_ids in fixed file",
          len({r["order_id"] for r in fixed}) == len(fixed))
    check("no non-standard payments left",
          {r["payment_method"] for r in fixed} <=
          {"Cash on Delivery", "Bank Transfer", "JazzCash", "Easypaisa", "Card"})
    check("no blank cities left", all(r["city"].strip() for r in fixed))
    check("all fixed dates are ISO",
          all(len(r["order_date"]) == 10 and r["order_date"][4] == "-"
              for r in fixed))
    check("276 fixed rows carry flags, 1,224 are OK",
          sum(1 for r in fixed if r["audit_flag"] != "OK") == 276
          and sum(1 for r in fixed if r["audit_flag"] == "OK") == 1224)
    check("9 zero-price rows still flagged (never invented)",
          sum(1 for r in fixed if r["unit_price"] == "0") == 9)
    check("22 orphan codes still flagged",
          sum(1 for r in fixed if r["product_code"] == "XX-9999") == 22)

    print("== SQLite + SQL checks ==")
    con = sqlite3.connect(DB)
    check("DB raw_orders = 1,524", con.execute("SELECT COUNT(*) FROM raw_orders").fetchone()[0] == 1524)
    check("DB fixed_orders = 1,500", con.execute("SELECT COUNT(*) FROM fixed_orders").fetchone()[0] == 1500)
    check("DB product_master = 41", con.execute("SELECT COUNT(*) FROM product_master").fetchone()[0] == 41)
    check("DB defect_register = 300", con.execute("SELECT COUNT(*) FROM defect_register").fetchone()[0] == 300)
    check("DB fixed total matches CSV",
          con.execute("SELECT SUM(total_amount) FROM fixed_orders").fetchone()[0] == fixed_total)
    lines = [l for l in open(ROOT / "sql" / "dq_checks.sql", encoding="utf-8")
             if not l.strip().startswith("--")]
    stmts = [s.strip() for s in "".join(lines).split(";") if s.strip().upper().startswith("SELECT")]
    expected = [24, 63, 27, 41, 12, 9, 18, 15, 22, 31]
    check("10 SQL checks in dq_checks.sql", len(stmts) == 10, f"got {len(stmts)}")
    for i, (q, e) in enumerate(zip(stmts, expected), 1):
        n = len(con.execute(q).fetchall())
        check(f"SQL DQ-{i:02d} returns {e} rows", n == e, f"got {n}")
    con.close()

    print("== workbook structure ==")
    wb = openpyxl.load_workbook(XLSX)
    check("workbook has Audit Summary / Defect Register / Fixed Data",
          wb.sheetnames == ["Audit Summary", "Defect Register", "Fixed Data"],
          str(wb.sheetnames))
    ws = wb["Audit Summary"]
    check("Summary KPI 'Rows received' is a live formula",
          isinstance(ws["B5"].value, str) and ws["B5"].value.startswith("="))
    check("Summary KPI 'Fixed total' is a live formula",
          isinstance(ws["B13"].value, str) and ws["B13"].value.startswith("=SUM("))
    check("Summary has a native bar chart", len(ws._charts) == 1)
    check("Defect Register sheet has 301 rows (header + 300)",
          wb["Defect Register"].max_row == 301)
    check("Fixed Data sheet has 1,501 rows (header + 1,500)",
          wb["Fixed Data"].max_row == 1501)
    check("Fixed Data totals are numbers, not text",
          isinstance(wb["Fixed Data"]["J2"].value, int))

    print("== report numbers ==")
    for needle in ("PKR 17,588,070", "PKR 17,350,640", "PKR 237,430",
                   "PKR 212,830", "PKR 24,600", "300 defects", "20.0%"):
        check(f"report states '{needle}'", needle in report)

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
