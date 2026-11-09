#!/usr/bin/env python3
"""Generate the SAMPLE client dataset for P13.

Fictional client: Al-Noor Traders, Lahore (general store). The file is
built clean first, then 300 defects are planted on disjoint rows so the
audit can be verified against an exact manifest. Nothing here is real
client data — the defects are the product, the file proves the audit.

Run: python3 src/generate_data.py
Outputs: data/raw/orders_SAMPLE.csv + data/raw/defect_manifest.json
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SEED = 20261109
N_ROWS = 1500

# Product master: code -> (name, category, price PKR)
PRODUCTS = [
    ("GR-101", "Basmati Rice 5kg", "Grocery", 2850),
    ("GR-102", "Cooking Oil 5L", "Grocery", 3450),
    ("GR-103", "Sugar 5kg", "Grocery", 720),
    ("GR-104", "Flour 10kg", "Grocery", 1150),
    ("GR-105", "Tea 900g", "Grocery", 1980),
    ("GR-106", "Lentils 2kg", "Grocery", 640),
    ("GR-107", "Salt 1kg", "Grocery", 120),
    ("GR-108", "Spices Mix 500g", "Grocery", 890),
    ("EL-201", "LED Bulb 12W", "Electronics", 450),
    ("EL-202", "Extension Board", "Electronics", 1250),
    ("EL-203", "Ceiling Fan", "Electronics", 6800),
    ("EL-204", "Iron", "Electronics", 4200),
    ("EL-205", "Kettle 1.7L", "Electronics", 3600),
    ("EL-206", "Charger Cable", "Electronics", 650),
    ("EL-207", "Power Bank 10000mAh", "Electronics", 3800),
    ("HK-301", "Dinner Set 72pc", "Home & Kitchen", 12500),
    ("HK-302", "Non-stick Pan", "Home & Kitchen", 2900),
    ("HK-303", "Water Cooler 20L", "Home & Kitchen", 1750),
    ("HK-304", "Bedsheet Double", "Home & Kitchen", 2400),
    ("HK-305", "Towel Set", "Home & Kitchen", 1450),
    ("HK-306", "Storage Box", "Home & Kitchen", 980),
    ("CL-401", "Men Kurta", "Clothing", 3200),
    ("CL-402", "Lawn Suit 3pc", "Clothing", 4500),
    ("CL-403", "Kids Frock", "Clothing", 1800),
    ("CL-404", "Shawl Wool", "Clothing", 2600),
    ("CL-405", "Socks Pack 6", "Clothing", 750),
    ("ST-501", "Notebook A4", "Stationery", 320),
    ("ST-502", "Ballpoint Pack 10", "Stationery", 280),
    ("ST-503", "Geometry Box", "Stationery", 540),
    ("ST-504", "File Folder", "Stationery", 150),
    ("ST-505", "Glue Stick", "Stationery", 180),
    ("PC-601", "Shampoo 400ml", "Personal Care", 980),
    ("PC-602", "Soap Pack 4", "Personal Care", 620),
    ("PC-603", "Toothpaste 150g", "Personal Care", 450),
    ("PC-604", "Face Wash", "Personal Care", 780),
    ("PC-605", "Hand Wash 500ml", "Personal Care", 520),
    ("PC-606", "Talcum Powder", "Personal Care", 390),
    ("PC-607", "Hair Oil 200ml", "Personal Care", 560),
    ("PC-608", "Lotion 200ml", "Personal Care", 690),
    ("PC-609", "Razor Pack", "Personal Care", 850),
    ("PC-610", "Sanitizer 250ml", "Personal Care", 420),
]
CATEGORIES = sorted({p[2] for p in PRODUCTS})
CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan"]
PAYMENTS = ["Cash on Delivery", "Bank Transfer", "JazzCash", "Easypaisa", "Card"]
FIRST = ["Ahmed", "Fatima", "Bilal", "Ayesha", "Usman", "Zainab", "Hassan",
         "Maryam", "Ali", "Sana", "Omar", "Hira", "Danish", "Rabia", "Imran",
         "Nida", "Saad", "Mahnoor", "Tariq", "Amna", "Kashif", "Sadia",
         "Waqas", "Mehwish", "Raza", "Farah", "Shahid", "Nadia", "Asif",
         "Kiran"]
LAST = ["Khan", "Ahmed", "Malik", "Hussain", "Ali", "Raza", "Iqbal",
        "Sheikh", "Butt", "Chaudhry", "Mirza", "Siddiqui", "Qureshi",
        "Rana", "Awan", "Abbasi", "Shah", "Javed", "Akhtar", "Nawaz"]

# Defect plan: type -> (count, severity). Planted on disjoint rows.
DEFECTS = {
    "duplicate_order_id": (24, "Critical"),
    "missing_email": (63, "High"),
    "missing_city": (41, "Medium"),
    "negative_quantity": (12, "Critical"),
    "zero_unit_price": (9, "Critical"),
    "total_mismatch": (18, "Critical"),
    "invalid_email": (27, "High"),
    "future_date": (10, "High"),
    "malformed_date": (5, "High"),
    "orphan_product_code": (22, "Critical"),
    "category_mismatch": (31, "Medium"),
    "nonstandard_payment": (38, "Medium"),
}


def main():
    rng = random.Random(SEED)
    start = date(2026, 1, 5)
    end = date(2026, 6, 30)
    span = (end - start).days

    customers = []
    for i in range(320):
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        email = f"{name.lower().replace(' ', '.')}{i}@example.com"
        customers.append((name, email))

    rows = []
    for i in range(N_ROWS):
        code, pname, cat, price = rng.choice(PRODUCTS)
        name, email = rng.choice(customers)
        qty = rng.randint(1, 12)
        d = start + timedelta(days=rng.randrange(span + 1))
        rows.append({
            "order_id": f"ANT-{10001 + i}",
            "order_date": d.isoformat(),
            "customer_name": name,
            "customer_email": email,
            "product_code": code,
            "product_name": pname,
            "category": cat,
            "quantity": str(qty),
            "unit_price": str(price),
            "total_amount": str(qty * price),
            "payment_method": rng.choice(PAYMENTS),
            "city": rng.choice(CITIES),
        })

    # Plant defects on disjoint row indexes.
    idx = list(range(N_ROWS))
    rng.shuffle(idx)
    manifest = {}
    cursor = 0

    def take(n):
        nonlocal cursor
        chosen = idx[cursor:cursor + n]
        cursor += n
        return chosen

    for dtype, (count, _sev) in DEFECTS.items():
        if dtype == "duplicate_order_id":
            # Duplicates are appended copies, not edits: pick 24 source rows.
            src = take(count)
            for j, s in enumerate(src):
                dup = dict(rows[s])
                rows.append(dup)  # same order_id, identical row
            manifest[dtype] = {"count": count, "order_ids": sorted(rows[s]["order_id"] for s in src)}
            continue
        chosen = take(count)
        manifest[dtype] = {"count": count, "order_ids": sorted(rows[i]["order_id"] for i in chosen)}
        for i in chosen:
            r = rows[i]
            if dtype == "missing_email":
                r["customer_email"] = ""
            elif dtype == "missing_city":
                r["city"] = ""
            elif dtype == "negative_quantity":
                q = int(r["quantity"])
                r["quantity"] = str(-q)
                r["total_amount"] = str(q * int(r["unit_price"]))  # stays consistent: only qty is wrong
            elif dtype == "zero_unit_price":
                r["unit_price"] = "0"
                r["total_amount"] = "0"
            elif dtype == "total_mismatch":
                r["total_amount"] = str(int(r["total_amount"]) + rng.choice([150, 500, 1000, 2500]))
            elif dtype == "invalid_email":
                r["customer_email"] = rng.choice([
                    r["customer_email"].replace("@", ""),
                    r["customer_email"].split("@")[0],
                    r["customer_email"].replace(".com", ""),
                ])
            elif dtype == "future_date":
                r["order_date"] = (date(2026, 9, 15) + timedelta(days=rng.randrange(20))).isoformat()
            elif dtype == "malformed_date":
                y, m, d = r["order_date"].split("-")
                r["order_date"] = f"{d}/{m}/{y}"  # DD/MM/YYYY instead of ISO
            elif dtype == "orphan_product_code":
                r["product_code"] = "XX-9999"
                r["product_name"] = "UNKNOWN PRODUCT"
            elif dtype == "category_mismatch":
                other = rng.choice([c for c in CATEGORIES if c != r["category"]])
                r["category"] = other
            elif dtype == "nonstandard_payment":
                r["payment_method"] = rng.choice(["cash", "Cash", "CASH", "cod", "COD", "bank", "jazzcash"])

    RAW.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with open(RAW / "orders_SAMPLE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (RAW / "defect_manifest.json").write_text(
        json.dumps({"seed": SEED, "rows": len(rows), "defects": manifest}, indent=2),
        encoding="utf-8")
    total = sum(v["count"] for v in manifest.values())
    print(f"wrote {len(rows)} rows (1500 base + 24 duplicates), {total} planted defects")
    for k, v in manifest.items():
        print(f"  {k}: {v['count']}")


if __name__ == "__main__":
    main()
