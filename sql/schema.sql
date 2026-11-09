-- P13 — Data Quality Audit Pack: star-lite schema
-- raw_orders: the file exactly as received (1,524 rows incl. duplicates)
-- fixed_orders: the file after the audit's fixes (1,500 rows)
-- product_master: the client's reference list (41 products)
-- defect_register: one row per defect found (300 rows)

CREATE TABLE IF NOT EXISTS raw_orders (
    order_id TEXT,
    order_date TEXT,
    customer_name TEXT,
    customer_email TEXT,
    product_code TEXT,
    product_name TEXT,
    category TEXT,
    quantity INTEGER,
    unit_price INTEGER,
    total_amount INTEGER,
    payment_method TEXT,
    city TEXT
);

CREATE TABLE IF NOT EXISTS fixed_orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT,
    customer_name TEXT,
    customer_email TEXT,
    product_code TEXT,
    product_name TEXT,
    category TEXT,
    quantity INTEGER,
    unit_price INTEGER,
    total_amount INTEGER,
    payment_method TEXT,
    city TEXT,
    audit_flag TEXT
);

CREATE TABLE IF NOT EXISTS product_master (
    product_code TEXT PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    unit_price INTEGER
);

CREATE TABLE IF NOT EXISTS defect_register (
    defect_id TEXT PRIMARY KEY,
    order_id TEXT,
    column_name TEXT,
    defect_type TEXT,
    severity TEXT,
    detail TEXT,
    fix_applied TEXT
);
