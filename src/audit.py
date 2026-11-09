#!/usr/bin/env python3
"""Audit the SAMPLE client file for P13.

Reads data/raw/orders_SAMPLE.csv cold — no knowledge of the planted
manifest — and detects every defect from the data itself, using the
product master in src/generate_data.py as the reference (a real client
supplies their own master file; here it ships inside the repo so the
audit is reproducible).

Run: python3 src/audit.py
Outputs: outputs/defect_register.csv + outputs/audit_summary.json
"""
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "raw" / "orders_SAMPLE.csv"
OUT = ROOT / "outputs"

# Product master duplicated here on purpose: the audit must not import
# the generator (a real audit runs against the client's own master file).
PRODUCTS = [
    ("GR-101", "Basmati Rice 5kg", "Grocery", 2850), ("GR-102", "Cooking Oil 5L", "Grocery", 3450),
    ("GR-103", "Sugar 5kg", "Grocery", 720), ("GR-104", "Flour 10kg", "Grocery", 1150),
    ("GR-105", "Tea 900g", "Grocery", 1980), ("GR-106", "Lentils 2kg", "Grocery", 640),
    ("GR-107", "Salt 1kg", "Grocery", 120), ("GR-108", "Spices Mix 500g", "Grocery", 890),
    ("EL-201", "LED Bulb 12W", "Electronics", 450), ("EL-202", "Extension Board", "Electronics", 1250),
    ("EL-203", "Ceiling Fan", "Electronics", 6800), ("EL-204", "Iron", "Electronics", 4200),
    ("EL-205", "Kettle 1.7L", "Electronics", 3600), ("EL-206", "Charger Cable", "Electronics", 650),
    ("EL-207", "Power Bank 10000mAh", "Electronics", 3800),
    ("HK-301", "Dinner Set 72pc", "Home & Kitchen", 12500), ("HK-302", "Non-stick Pan", "Home & Kitchen", 2900),
    ("HK-303", "Water Cooler 20L", "Home & Kitchen", 1750), ("HK-304", "Bedsheet Double", "Home & Kitchen", 2400),
    ("HK-305", "Towel Set", "Home & Kitchen", 1450), ("HK-306", "Storage Box", "Home & Kitchen", 980),
    ("CL-401", "Men Kurta", "Clothing", 3200), ("CL-402", "Lawn Suit 3pc", "Clothing", 4500),
    ("CL-403", "Kids Frock", "Clothing", 1800), ("CL-404", "Shawl Wool", "Clothing", 2600),
    ("CL-405", "Socks Pack 6", "Clothing", 750),
    ("ST-501", "Notebook A4", "Stationery", 320), ("ST-502", "Ballpoint Pack 10", "Stationery", 280),
    ("ST-503", "Geometry Box", "Stationery", 540), ("ST-504", "File Folder", "Stationery", 150),
    ("ST-505", "Glue Stick", "Stationery", 180),
    ("PC-601", "Shampoo 400ml", "Personal Care", 980), ("PC-602", "Soap Pack 4", "Personal Care", 620),
    ("PC-603", "Toothpaste 150g", "Personal Care", 450), ("PC-604", "Face Wash", "Personal Care", 780),
    ("PC-605", "Hand Wash 500ml", "Personal Care", 520), ("PC-606", "Talcum Powder", "Personal Care", 390),
    ("PC-607", "Hair Oil 200ml", "Personal Care", 560), ("PC-608", "Lotion 200ml", "Personal Care", 690),
    ("PC-609", "Razor Pack", "Personal Care", 850), ("PC-610", "Sanitizer 250ml", "Personal Care", 420),
]
MASTER = {code: (name, cat, price) for code, name, cat, price in PRODUCTS}
PAYMENTS = {"Cash on Delivery", "Bank Transfer", "JazzCash", "Easypaisa", "Card"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FILE_END = date(2026, 6, 30)  # last date the file claims to cover

SEVERITY = {
    "duplicate_order_id": "Critical", "negative_quantity": "Critical",
    "zero_unit_price": "Critical", "total_mismatch": "Critical",
    "orphan_product_code": "Critical", "missing_email": "High",
    "invalid_email": "High", "future_date": "High", "malformed_date": "High",
    "missing_city": "Medium", "category_mismatch": "Medium",
    "nonstandard_payment": "Medium",
}
FIX = {
    "duplicate_order_id": "Drop the later copy; keep the first occurrence.",
    "missing_email": "LEFT BLANK — ask the customer; never invent an email.",
    "missing_city": "Set to 'Unknown' in the fixed file.",
    "negative_quantity": "Take the absolute value; recompute the total.",
    "zero_unit_price": "LEFT AT 0 — price must come from the client.",
    "total_mismatch": "Recompute total = quantity x unit price.",
    "invalid_email": "LEFT AS-IS — flag for the client to correct.",
    "future_date": "LEFT AS-IS — flag for the client to verify.",
    "malformed_date": "Re-parsed DD/MM/YYYY to ISO (YYYY-MM-DD).",
    "orphan_product_code": "LEFT AS-IS — code is not in the product master.",
    "category_mismatch": "Reset to the product master's category.",
    "nonstandard_payment": "Standardised to the canonical payment name.",
}


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    defects = []  # (order_id, column, type, detail)

    def add(oid, col, dtype, detail):
        defects.append({"order_id": oid, "column": col, "defect_type": dtype,
                        "severity": SEVERITY[dtype], "detail": detail,
                        "fix_applied": FIX[dtype]})

    seen_ids = Counter()
    for r in rows:
        seen_ids[r["order_id"]] += 1
    for oid, n in seen_ids.items():
        if n > 1:
            add(oid, "order_id", "duplicate_order_id",
                f"order_id appears {n} times in the file")

    seen_first = set()
    for r in rows:
        oid = r["order_id"]
        is_dup_copy = oid in seen_first
        seen_first.add(oid)
        if is_dup_copy:
            continue  # a duplicate copy carries the same defects as its original; count once
        if not r["customer_email"].strip():
            add(oid, "customer_email", "missing_email", "email is blank")
        elif not EMAIL_RE.match(r["customer_email"].strip()):
            add(oid, "customer_email", "invalid_email",
                f"'{r['customer_email']}' is not a valid email address")
        if not r["city"].strip():
            add(oid, "city", "missing_city", "city is blank")
        try:
            qty = int(r["quantity"])
        except ValueError:
            qty = None
            add(oid, "quantity", "negative_quantity", f"quantity '{r['quantity']}' is not a number")
        if qty is not None and qty <= 0:
            add(oid, "quantity", "negative_quantity", f"quantity is {qty}")
        try:
            price = int(r["unit_price"])
        except ValueError:
            price = None
        if price is not None and price == 0:
            add(oid, "unit_price", "zero_unit_price", "unit price is 0")
        try:
            total = int(r["total_amount"])
        except ValueError:
            total = None
        if qty is not None and price is not None and total is not None:
            # Only run the derived check when its inputs are sane: a row
            # whose quantity is already flagged must not also count as a
            # mismatch — one root cause, one register row.
            if qty > 0 and price >= 0 and total != qty * price:
                add(oid, "total_amount", "total_mismatch",
                    f"total {total} != quantity {qty} x price {price} = {qty * price}")
        d = r["order_date"].strip()
        if re.match(r"^\d{2}/\d{2}/\d{4}$", d):
            add(oid, "order_date", "malformed_date",
                f"date '{d}' is DD/MM/YYYY, not ISO YYYY-MM-DD")
        else:
            try:
                parsed = date.fromisoformat(d)
                if parsed > FILE_END:
                    add(oid, "order_date", "future_date",
                        f"date {d} is after the file's last date {FILE_END}")
            except ValueError:
                add(oid, "order_date", "malformed_date", f"date '{d}' does not parse")
        code = r["product_code"].strip()
        if code not in MASTER:
            add(oid, "product_code", "orphan_product_code",
                f"code '{code}' is not in the product master")
        elif r["category"].strip() != MASTER[code][1]:
            add(oid, "category", "category_mismatch",
                f"category '{r['category']}' disagrees with the master "
                f"('{MASTER[code][1]}') for {code}")
        if r["payment_method"].strip() not in PAYMENTS:
            add(oid, "payment_method", "nonstandard_payment",
                f"payment '{r['payment_method']}' is not a canonical value")

    defects.sort(key=lambda d: (d["order_id"], d["defect_type"]))
    for i, d in enumerate(defects, 1):
        d["defect_id"] = f"DQ-{i:04d}"
    fields = ["defect_id", "order_id", "column", "defect_type", "severity", "detail", "fix_applied"]
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "defect_register.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(defects)

    by_type = Counter(d["defect_type"] for d in defects)
    by_sev = Counter(d["severity"] for d in defects)
    by_col = Counter(d["column"] for d in defects)
    affected = len({d["order_id"] for d in defects})
    summary = {
        "rows_received": len(rows),
        "unique_order_ids": len(seen_ids),
        "total_defects": len(defects),
        "affected_orders": affected,
        "clean_orders": len(seen_ids) - affected,
        "by_type": dict(sorted(by_type.items())),
        "by_severity": dict(sorted(by_sev.items())),
        "by_column": dict(sorted(by_col.items())),
    }
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{len(rows)} rows audited, {len(defects)} defects on {affected} orders")
    for k, v in sorted(by_type.items()):
        print(f"  {k}: {v}")
    print(f"  severity: {dict(by_sev)}")


if __name__ == "__main__":
    main()
