#!/usr/bin/env python3
"""Apply the audit's fixes for P13.

Rules (exactly as written in the defect register's fix_applied column):
- duplicates: keep the first occurrence, drop the rest
- missing city: 'Unknown' | malformed date: re-parse DD/MM/YYYY to ISO
- negative quantity: absolute value, recompute total
- total mismatch: recompute total = quantity x unit price
- category mismatch: reset to the product master's category
- non-standard payment: standardise to the canonical name
- missing/invalid email, zero price, future date, orphan code: LEFT AS-IS,
  flagged in audit_flag — the audit never invents data the client owns.

Run: python3 src/fix_data.py
Output: data/processed/orders_FIXED.csv (fixed rows + audit_flag column)
"""
import csv
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
REG = ROOT / "outputs" / "defect_register.csv"
OUT = ROOT / "data" / "processed" / "orders_FIXED.csv"

MASTER_CAT = {}  # category per product code (from the client's product master)
MASTER = {
    "GR-101": "Grocery", "GR-102": "Grocery", "GR-103": "Grocery", "GR-104": "Grocery",
    "GR-105": "Grocery", "GR-106": "Grocery", "GR-107": "Grocery", "GR-108": "Grocery",
    "EL-201": "Electronics", "EL-202": "Electronics", "EL-203": "Electronics",
    "EL-204": "Electronics", "EL-205": "Electronics", "EL-206": "Electronics",
    "EL-207": "Electronics",
    "HK-301": "Home & Kitchen", "HK-302": "Home & Kitchen", "HK-303": "Home & Kitchen",
    "HK-304": "Home & Kitchen", "HK-305": "Home & Kitchen", "HK-306": "Home & Kitchen",
    "CL-401": "Clothing", "CL-402": "Clothing", "CL-403": "Clothing",
    "CL-404": "Clothing", "CL-405": "Clothing",
    "ST-501": "Stationery", "ST-502": "Stationery", "ST-503": "Stationery",
    "ST-504": "Stationery", "ST-505": "Stationery",
    "PC-601": "Personal Care", "PC-602": "Personal Care", "PC-603": "Personal Care",
    "PC-604": "Personal Care", "PC-605": "Personal Care", "PC-606": "Personal Care",
    "PC-607": "Personal Care", "PC-608": "Personal Care", "PC-609": "Personal Care",
    "PC-610": "Personal Care",
}
PAYMENT_MAP = {"cash": "Cash on Delivery", "Cash": "Cash on Delivery",
               "CASH": "Cash on Delivery", "cod": "Cash on Delivery",
               "COD": "Cash on Delivery", "bank": "Bank Transfer",
               "jazzcash": "JazzCash"}


def main():
    rows = list(csv.DictReader(open(RAW, encoding="utf-8")))
    register = list(csv.DictReader(open(REG, encoding="utf-8")))
    by_order = {}
    for d in register:
        by_order.setdefault(d["order_id"], []).append(d["defect_type"])

    fixed, seen = [], set()
    dropped = 0
    for r in rows:
        oid = r["order_id"]
        if oid in seen:
            dropped += 1
            continue
        seen.add(oid)
        flags = []
        types = by_order.get(oid, [])
        if "missing_city" in types:
            r["city"] = "Unknown"
            flags.append("city set to Unknown")
        if "malformed_date" in types:
            d, m, y = r["order_date"].split("/")
            r["order_date"] = f"{y}-{m}-{d}"
            flags.append("date re-parsed to ISO")
        if "negative_quantity" in types:
            r["quantity"] = str(abs(int(r["quantity"])))
            flags.append("quantity made positive")
        if "category_mismatch" in types:
            r["category"] = MASTER[r["product_code"]]
            flags.append("category reset to master")
        if "nonstandard_payment" in types:
            r["payment_method"] = PAYMENT_MAP[r["payment_method"]]
            flags.append("payment standardised")
        if "total_mismatch" in types or "negative_quantity" in types:
            r["total_amount"] = str(int(r["quantity"]) * int(r["unit_price"]))
            if "total_mismatch" in types:
                flags.append("total recomputed")
        for t in ("missing_email", "invalid_email", "zero_unit_price",
                  "future_date", "orphan_product_code"):
            if t in types:
                flags.append(f"FLAGGED: {t.replace('_', ' ')} — needs client")
        r["audit_flag"] = "; ".join(flags) if flags else "OK"
        fixed.append(r)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) + ["audit_flag"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(fixed)
    flagged = sum(1 for r in fixed if r["audit_flag"] != "OK")
    print(f"fixed file: {len(fixed)} rows ({dropped} duplicates dropped), "
          f"{flagged} rows carry flags, {len(fixed) - flagged} clean")


if __name__ == "__main__":
    main()
