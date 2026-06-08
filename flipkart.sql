CREATE TABLE flipkart (
    uniq_id                  VARCHAR(64)       PRIMARY KEY,
    crawl_timestamp          TIMESTAMP,
    product_url              TEXT,
    product_name             TEXT,
    product_category_tree    TEXT,
    pid                      VARCHAR(32),
    retail_price             NUMERIC(12, 2),
    discounted_price         NUMERIC(12, 2),
    image                    TEXT,
    is_fk_advantage_product  BOOLEAN,
    description              TEXT,
    product_rating           VARCHAR(50),
    overall_rating           VARCHAR(50),
    brand                    VARCHAR(255),
    product_specifications   TEXT
);
SELECT * FROM flipkart
copy flipkart (
    uniq_id, crawl_timestamp, product_url, product_name,
    product_category_tree, pid, retail_price, discounted_price,
    image, is_fk_advantage_product, description,
    product_rating, overall_rating, brand, product_specifications
)
FROM 'D:/flipkart_com-ecommerce_sample.csv'
WITH (
    FORMAT CSV,
    HEADER TRUE,
    DELIMITER ',',
    NULL '',
    QUOTE '"',
    ENCODING 'UTF8'
);

-- Q1. Product Count per Category (Top 15)

SELECT
    TRIM(SUBSTRING_INDEX(REPLACE(product_category_tree, '"', ''), '>>', 1)) AS main_category,
    COUNT(*) AS product_count
FROM flipkart
GROUP BY main_category
ORDER BY product_count DESC
LIMIT 15;


--Q2. Average Price and Discount per Category

SELECT
    main_category,
    ROUND(AVG(retail_price), 2)      AS avg_retail_price,
    ROUND(AVG(discounted_price), 2)  AS avg_discounted_price,
    ROUND(AVG((retail_price - discounted_price) * 100.0 / retail_price), 2) AS avg_discount_pct
FROM flipkart
WHERE retail_price > 0
GROUP BY main_category
ORDER BY avg_discount_pct DESC;


--- Q3. Products with 0% vs >50% Discount

SELECT
    CASE
        WHEN (retail_price - discounted_price) * 100.0 / retail_price = 0   THEN 'No Discount (0%)'
        WHEN (retail_price - discounted_price) * 100.0 / retail_price <= 25  THEN 'Low (1–25%)'
        WHEN (retail_price - discounted_price) * 100.0 / retail_price <= 50  THEN 'Medium (26–50%)'
        WHEN (retail_price - discounted_price) * 100.0 / retail_price <= 75  THEN 'High (51–75%)'
        ELSE 'Very High (>75%)'
    END AS discount_segment,
    COUNT(*) AS product_count
FROM flipkart
WHERE retail_price > 0
GROUP BY discount_segment
ORDER BY product_count DESC;


--- Q4. Top 10 Products by Absolute Savings (₹)

SELECT
    product_name,
    brand,
    main_category,
    retail_price,
    discounted_price,
    (retail_price - discounted_price) AS savings_amount
FROM flipkart
WHERE retail_price > 0
ORDER BY savings_amount DESC
LIMIT 10;


---Q5. Top 20 Brands by Number of Listings

SELECT brand, COUNT(*) AS listings
FROM flipkart
WHERE brand IS NOT NULL
GROUP BY brand
ORDER BY listings DESC
LIMIT 20;


---

--Q6. Brands with Highest Avg Discount (min 30 products)

SELECT
    brand,
    COUNT(*) AS total_products,
    ROUND(AVG((retail_price - discounted_price) * 100.0 / retail_price), 2) AS avg_discount_pct
FROM flipkart
WHERE retail_price > 0 AND brand IS NOT NULL
GROUP BY brand
HAVING total_products >= 30
ORDER BY avg_discount_pct DESC
LIMIT 15;


--Q7. Average Rating per Category (min 50 rated products)

SELECT
    main_category,
    COUNT(rating)          AS rated_products,
    ROUND(AVG(CAST(rating AS FLOAT)), 2) AS avg_rating
FROM flipkart
WHERE rating NOT LIKE '%No rating%' AND rating IS NOT NULL
GROUP BY main_category
HAVING rated_products >= 50
ORDER BY avg_rating DESC;


### Q8. FK Advantage vs Regular: Price & Discount Comparison

SELECT
    is_FK_Advantage_product,
    COUNT(*)                                                                  AS total_products,
    ROUND(AVG(retail_price), 2)                                               AS avg_retail_price,
    ROUND(AVG(discounted_price), 2)                                           AS avg_discounted_price,
    ROUND(AVG((retail_price - discounted_price) * 100.0 / retail_price), 2)  AS avg_discount_pct,
    ROUND(AVG(CAST(rating AS FLOAT)), 2)                                      AS avg_rating
FROM flipkart
WHERE retail_price > 0
GROUP BY is_FK_Advantage_product;


---

### Q9. Price Bucket Distribution

SELECT
    CASE
        WHEN discounted_price BETWEEN 0    AND 500   THEN '₹0–500'
        WHEN discounted_price BETWEEN 501  AND 1000  THEN '₹501–1K'
        WHEN discounted_price BETWEEN 1001 AND 2000  THEN '₹1K–2K'
        WHEN discounted_price BETWEEN 2001 AND 5000  THEN '₹2K–5K'
        WHEN discounted_price BETWEEN 5001 AND 10000 THEN '₹5K–10K'
        ELSE '₹10K+'
    END AS price_bucket,
    COUNT(*) AS product_count
FROM flipkart
WHERE discounted_price IS NOT NULL
GROUP BY price_bucket
ORDER BY MIN(discounted_price);
```

---

### Q10. Category-wise Price Range (Min, Max, Avg)
```sql
SELECT
    main_category,
    COUNT(*)                           AS total_products,
    MIN(discounted_price)              AS min_price,
    MAX(discounted_price)              AS max_price,
    ROUND(AVG(discounted_price), 2)    AS avg_price,
    ROUND(STDDEV(discounted_price), 2) AS price_std_dev
FROM flipkart
WHERE discounted_price IS NOT NULL
GROUP BY main_category
ORDER BY avg_price DESC
LIMIT 15;
```

---

### Q11. Top FK Advantage Categories
```sql
SELECT
    main_category,
    COUNT(*) AS fk_advantage_products
FROM flipkart
WHERE is_FK_Advantage_product = TRUE
GROUP BY main_category
ORDER BY fk_advantage_products DESC
LIMIT 10;
```

---

### Q12. % of Products with Ratings per Category
```sql
SELECT
    main_category,
    COUNT(*)                                                          AS total,
    SUM(CASE WHEN rating NOT LIKE '%No rating%' THEN 1 ELSE 0 END)  AS rated,
    ROUND(100.0 * SUM(CASE WHEN rating NOT LIKE '%No rating%' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_rated
FROM flipkart
GROUP BY main_category
ORDER BY pct_rated DESC
LIMIT 15;
```

---

### Q13. Products Crawled per Month
```sql
SELECT
    DATE_FORMAT(crawl_timestamp, '%Y-%m') AS crawl_month,
    COUNT(*)                               AS products_crawled
FROM flipkart
GROUP BY crawl_month
ORDER BY crawl_month;
```

---

### Q14. Brands with Best Avg Rating (min 30 rated products)
```sql
SELECT
    brand,
    COUNT(rating)                           AS rated_count,
    ROUND(AVG(CAST(rating AS FLOAT)), 2)    AS avg_rating
FROM flipkart
WHERE rating NOT LIKE '%No rating%'
  AND brand IS NOT NULL
GROUP BY brand
HAVING rated_count >= 30
ORDER BY avg_rating DESC
LIMIT 15;
```

---

### Q15. Rating vs Price Correlation Check
```sql
SELECT
    CASE
        WHEN discounted_price BETWEEN 0    AND 500   THEN '₹0–500'
        WHEN discounted_price BETWEEN 501  AND 1000  THEN '₹501–1K'
        WHEN discounted_price BETWEEN 1001 AND 2000  THEN '₹1K–2K'
        WHEN discounted_price BETWEEN 2001 AND 5000  THEN '₹2K–5K'
        WHEN discounted_price BETWEEN 5001 AND 10000 THEN '₹5K–10K'
        ELSE '₹10K+'
    END AS price_bucket,
    COUNT(rating)                        AS rated_products,
    ROUND(AVG(CAST(rating AS FLOAT)), 2) AS avg_rating
FROM flipkart
WHERE rating NOT LIKE '%No rating%' AND discounted_price IS NOT NULL
GROUP BY price_bucket
ORDER BY MIN(discounted_price);
```
