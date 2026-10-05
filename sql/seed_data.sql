.mode csv
.import --skip 1 data/customers.csv customers
.import --skip 1 data/products.csv products
.import --skip 1 data/orders.csv orders

-- .import loads blank cells as '' (not NULL); convert them before any report
UPDATE orders SET discount_pct = NULL WHERE discount_pct = '';
UPDATE orders SET rating       = NULL WHERE rating = '';

-- Verification (expected 45 / 16 / 180)
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM orders;
