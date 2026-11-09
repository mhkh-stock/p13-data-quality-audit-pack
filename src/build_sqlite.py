#!/usr/bin/env python3
"""Load the P13 audit into SQLite (run: python3 src/build_sqlite.py).

Builds data/processed/orders.db from sql/schema.sql:
raw_orders (1,524) + fixed_orders (1,500) + product_master (41)
+ defect_register (300). The .db is NOT uploaded to GitHub — it is
rebuildable from the pushed scripts and CSVs.
"""
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DB = ROOT / "data" / "processed" / "orders.db"


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))

    raw = list(csv.DictReader(open(ROOT / "data" / "raw" / "orders_SAMPLE.csv", encoding="utf-8")))
    con.executemany(
        "INSERT INTO raw_orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [[r[k] for k in ("order_id", "order_date", "customer_name", "customer_email",
                        "product_code", "product_name", "category", "quantity",
                        "unit_price", "total_amount", "payment_method", "city")] for r in raw])

    fixed = list(csv.DictReader(open(ROOT / "data" / "processed" / "orders_FIXED.csv", encoding="utf-8")))
    con.executemany(
        "INSERT INTO fixed_orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [[r[k] for k in ("order_id", "order_date", "customer_name", "customer_email",
                        "product_code", "product_name", "category", "quantity",
                        "unit_price", "total_amount", "payment_method", "city", "audit_flag")] for r in fixed])

    from audit import PRODUCTS  # the master, shared with the audit script
    con.executemany("INSERT INTO product_master VALUES (?,?,?,?)", PRODUCTS)

    reg = list(csv.DictReader(open(ROOT / "outputs" / "defect_register.csv", encoding="utf-8")))
    con.executemany(
        "INSERT INTO defect_register VALUES (?,?,?,?,?,?,?)",
        [[r[k] for k in ("defect_id", "order_id", "column", "defect_type",
                        "severity", "detail", "fix_applied")] for r in reg])
    con.commit()
    for t in ("raw_orders", "fixed_orders", "product_master", "defect_register"):
        print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
