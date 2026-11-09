-- P13 — Data Quality Audit Pack: the 10 SQL checks the client keeps.
-- Run them on any new file the same way: load it into raw_orders, then
-- run this file. Every query returns 0 rows when the file is clean.
-- (SQLite syntax; the same logic ports to any warehouse in minutes.)

-- DQ-01: duplicate order_id values in the file as received
SELECT order_id, COUNT(*) AS occurrences
FROM raw_orders GROUP BY order_id HAVING COUNT(*) > 1;

-- DQ-02: blank customer emails
SELECT order_id FROM raw_orders WHERE TRIM(customer_email) = '';

-- DQ-03: emails that do not look like an email address
SELECT order_id, customer_email FROM raw_orders
WHERE TRIM(customer_email) <> ''
  AND customer_email NOT LIKE '%_@_%._%';

-- DQ-04: blank city
SELECT order_id FROM raw_orders WHERE TRIM(city) = '';

-- DQ-05: quantity zero or negative
SELECT order_id, quantity FROM raw_orders WHERE quantity <= 0;

-- DQ-06: unit price zero (or negative — a price is never free here)
SELECT order_id, unit_price FROM raw_orders WHERE unit_price <= 0;

-- DQ-07: total does not equal quantity x unit price
-- (only where quantity and price are themselves sane — see audit.py)
SELECT order_id, quantity, unit_price, total_amount,
       quantity * unit_price AS expected_total
FROM raw_orders
WHERE quantity > 0 AND unit_price >= 0
  AND total_amount <> quantity * unit_price;

-- DQ-08: order dates outside the file's stated window (Jan–Jun 2026)
-- or not in ISO YYYY-MM-DD form
SELECT order_id, order_date FROM raw_orders
WHERE order_date NOT LIKE '____-__-__'
   OR order_date < '2026-01-01' OR order_date > '2026-06-30';

-- DQ-09: product codes missing from the product master
SELECT order_id, product_code FROM raw_orders
WHERE product_code NOT IN (SELECT product_code FROM product_master);

-- DQ-10: category disagrees with the product master
SELECT r.order_id, r.product_code, r.category AS file_category,
       m.category AS master_category
FROM raw_orders r JOIN product_master m USING (product_code)
WHERE r.category <> m.category;
