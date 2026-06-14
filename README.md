# 🛒 Flipkart E-Commerce Data Analysis Project (2015–2016)

> A full-stack data analysis project examining 20,000 Flipkart product listings to uncover pricing strategies, discount patterns, brand performance, category intelligence, and product quality signals on India's leading e-commerce platform.

---

## 📁 Project Structure

```
flipkart-data-analysis/
│
├── data/
│   └── flipkart_com-ecommerce_sample.csv   # 20,000 product listings (15 columns)
│
├── sql/
│   ├── postgresql_setup.sql                # CREATE TABLE + \copy + derived columns
│   └── flipkart_queries.sql                # 15 analytical SQL queries
│
├── python/
│   └── flipkart_eda.py                     # Full EDA script (cleaning, charts, analysis)
│
├── powerbi/
│   └── Flipkart_Dashboard_Guide.md         # Power BI visual guide + DAX measures
│
├── report/
│   └── Flipkart_Analysis_Report.docx       # Full written analysis report
│
└── README.md
```

---

## 📊 Dataset Overview

| File | Rows | Columns | Crawl Period |
|---|---|---|---|
| `flipkart_com-ecommerce_sample.csv` | 20,000 | 15 | Dec 2015 – Jun 2016 |

### Column Reference

| Column | Type | Description |
|---|---|---|
| `uniq_id` | VARCHAR | Unique product identifier — Primary Key |
| `crawl_timestamp` | TEXT | Date and time the product was scraped (format: `YYYY-MM-DD HH:MM:SS +0000`) |
| `product_url` | TEXT | Full Flipkart product page URL |
| `product_name` | TEXT | Product title as displayed on Flipkart |
| `product_category_tree` | TEXT | Hierarchical category path (e.g. `["Clothing >> Women's Clothing >> ..."]`) |
| `pid` | VARCHAR | Flipkart internal platform product ID |
| `retail_price` | NUMERIC | Original MRP as listed on the product page |
| `discounted_price` | NUMERIC | Actual selling price at time of crawl |
| `image` | TEXT | Primary product image URL |
| `is_FK_Advantage_product` | BOOLEAN | TRUE if part of Flipkart Advantage fulfilment programme |
| `description` | TEXT | Full product description from the listing |
| `product_rating` | VARCHAR | Numeric rating (e.g. `4.2`) or `No rating available` |
| `overall_rating` | VARCHAR | Secondary aggregate rating field |
| `brand` | VARCHAR | Brand or manufacturer name |
| `product_specifications` | TEXT | Semi-structured JSON product attribute string |

### Derived Columns (added during analysis)

| Column | Formula | Description |
|---|---|---|
| `main_category` | `SPLIT_PART(product_category_tree, ' >> ', 1)` | First-level category (e.g. Clothing, Jewellery) |
| `discount_pct` | `(retail_price - discounted_price) / retail_price × 100` | Discount percentage off MRP |
| `savings_amt` | `retail_price - discounted_price` | Absolute savings in rupees |

---

## 🎯 Problem Statement

> **"Analysing Flipkart's Product Catalogue to Uncover Pricing Strategies, Discount Patterns, Brand Performance, and Category-Level Insights That Drive Customer Value and Business Revenue on India's Leading E-Commerce Platform."**

---

## ❓ Research Questions

### Category Analysis
1. Which product categories have the most listings on Flipkart?
2. What is the average discounted price per category?
3. Which categories offer the highest average discount percentage?
4. How are products distributed across price buckets (budget / mid / premium)?
5. Which categories have the widest price range (min vs. max)?

### Pricing & Discount Analysis
6. What is the overall distribution of discount percentages?
7. How many products have zero discount vs. more than 50% discount?
8. Which specific products offer the highest absolute savings (Rs. saved)?
9. Is there a correlation between retail price and discount percentage?
10. What does the price bucket distribution look like across the full catalogue?

### Brand Analysis
11. Which are the top 20 most-listed brands on Flipkart?
12. Which brands offer the highest average discount?
13. Which brands have the highest average product ratings?
14. What is the average price range per top brand?
15. Which brands dominate each major category?

### Ratings & Quality
16. What share of products have no rating at all?
17. Which categories have the best and worst average ratings?
18. Do higher-priced products tend to have better ratings?
19. Do FK Advantage products receive better ratings?
20. What is the distribution of ratings from 1.0 to 5.0?

### FK Advantage
21. What share of products are FK Advantage products?
22. Do FK Advantage products have lower or higher average prices?
23. Which categories have the most FK Advantage products?
24. Do FK Advantage products offer different discount levels?

---

## 🗄️ Database Setup (PostgreSQL)

### Prerequisites
- PostgreSQL 13+
- psql command-line OR pgAdmin / DBeaver

### Step 1 — Run setup script
```bash
psql -U your_username -d your_database -f sql/postgresql_setup.sql
```

### Step 2 — Update file path
Edit the `\copy` command in `postgresql_setup.sql`:
```sql
-- Change this to your actual CSV file path:
FROM '/absolute/path/to/flipkart_com-ecommerce_sample.csv'
```

### Step 3 — Verify load
```sql
SELECT COUNT(*) FROM flipkart;
-- Expected: 20,000
```

### Step 4 — Add derived columns (run once after loading)
```sql
ALTER TABLE flipkart
    ADD COLUMN IF NOT EXISTS discount_pct  NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS savings_amt   NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS main_category TEXT;

UPDATE flipkart
SET
    discount_pct  = ROUND(((retail_price - discounted_price) * 100.0
                    / NULLIF(retail_price, 0))::NUMERIC, 2),
    savings_amt   = retail_price - discounted_price,
    main_category = TRIM(SPLIT_PART(
                        REPLACE(REPLACE(product_category_tree, '["', ''), '"]', ''),
                        ' >> ', 1));
```

### Important PostgreSQL Notes
> These fixes apply specifically to PostgreSQL (not MySQL):

| Issue | Wrong (MySQL) | Correct (PostgreSQL) |
|---|---|---|
| Extract category | `SUBSTRING_INDEX(col, '>>', 1)` | `SPLIT_PART(col, ' >> ', 1)` |
| Round a float | `ROUND(AVG(col), 2)` | `ROUND(AVG(col)::NUMERIC, 2)` |
| Format date | `DATE_FORMAT(col, '%Y-%m')` | `TO_CHAR(col::TIMESTAMPTZ, 'YYYY-MM')` |
| FK Advantage column | `is_fk_advantage_product` | `"is_FK_Advantage_product"` (quoted) |
| HAVING on alias | `HAVING count >= 30` | Wrap in CTE, then `WHERE count >= 30` |
| LIKE on rating | `WHERE rating NOT LIKE '%No rating%'` | `WHERE product_rating ~ '^\d+(\.\d+)?$'` |

### Alternative — Python loading
```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://username:password@localhost:5432/your_db")

fk = pd.read_csv("flipkart_com-ecommerce_sample.csv")
fk['retail_price']     = pd.to_numeric(fk['retail_price'], errors='coerce')
fk['discounted_price'] = pd.to_numeric(fk['discounted_price'], errors='coerce')
fk['crawl_timestamp']  = pd.to_datetime(fk['crawl_timestamp'].str[:19])
fk.to_sql('flipkart', engine, if_exists='replace', index=False, chunksize=1000)
print("Loaded:", len(fk), "rows")
```

---

## 🐍 Python EDA

### Requirements
```bash
pip install pandas numpy matplotlib seaborn
```

### Run
```bash
python python/flipkart_eda.py
```

### Charts Generated
| File | Description |
|---|---|
| `cat_product_count.png` | Top 15 categories by listing count |
| `price_distribution.png` | Discounted price distribution (log scale) |
| `discount_distribution.png` | Discount % histogram with KDE |
| `rating_distribution.png` | Rating value bar chart (1–5) |
| `price_bucket.png` | Products per price bucket |
| `fk_advantage_pie.png` | FK Advantage vs Regular share |
| `cat_avg_price.png` | Average selling price per category |
| `cat_avg_discount.png` | Average discount % per category |
| `cat_avg_rating.png` | Average rating per category (min. 50 products) |
| `top_brands.png` | Top 20 brands by listing volume |
| `brand_avg_discount.png` | Top 15 brands by average discount |
| `price_vs_discount_scatter.png` | Retail price vs. discount % scatter |
| `discount_segments.png` | Products by discount tier (0% / low / medium / high) |
| `fk_advantage_categories.png` | Top categories for FK Advantage products |
| `rating_by_price_bucket.png` | Rating boxplot by price bucket |
| `crawl_trend.png` | Products crawled per day over time |

---

## 📊 Power BI Dashboard — 5 Pages

| Page | Focus | Key Visuals |
|---|---|---|
| **1 — Overview** | Executive KPIs | Cards (products, categories, brands, avg discount), bar chart, donut |
| **2 — Pricing** | Discount analysis | Clustered bar (price vs. MRP), histogram (discount %), treemap (savings) |
| **3 — Brands** | Brand intelligence | Bar (top brands), scatter (price vs. rating), matrix (brand × category) |
| **4 — Ratings** | Quality analysis | Bar (rating distribution), gauge (overall avg), box plot (rating by price) |
| **5 — Categories** | Category deep dive | Treemap (hierarchy), funnel (price buckets), 100% stacked (discount mix) |

### Key DAX Measures
```dax
-- Average Discount %
Avg Discount % = AVERAGE(flipkart[discount_pct])

-- Total Savings (Rs.)
Total Savings =
SUMX(flipkart, flipkart[retail_price] - flipkart[discounted_price])

-- % Products with Rating
Pct Rated =
DIVIDE(
    CALCULATE(COUNTROWS(flipkart), NOT(ISBLANK(flipkart[rating]))),
    COUNTROWS(flipkart), 0) * 100

-- FK Advantage Share
FK Advantage % =
DIVIDE(
    CALCULATE(COUNTROWS(flipkart), flipkart[is_FK_Advantage_product] = TRUE()),
    COUNTROWS(flipkart), 0) * 100

-- Avg Selling Price
Avg Selling Price = AVERAGE(flipkart[discounted_price])
```

---

## 📈 Key Findings

| Metric | Value |
|---|---|
| Total products | 20,000 |
| Total categories | 266 |
| Total unique brands | 3,499 |
| Dominant category | **Clothing — 6,198 products (31.0%)** |
| Average discount | **40.5%** (median 45.0%) |
| Products with >50% discount | 8,786 (43.9%) |
| Products with zero discount | 2,287 (11.5%) |
| Products with NO rating | **18,151 (90.8%)** ← critical finding |
| Best-rated category | Kitchen & Dining (avg 4.38) |
| Worst-rated category | Tools & Hardware (avg 3.38) |
| FK Advantage products | 785 (3.9% of catalogue) |
| Most common price range | Rs. 0–500 (47% of products) |
| Average retail (MRP) price | Rs. 2,979 |
| Average selling price | Rs. 1,973 |

---

## 🔧 Data Quality Notes

- `retail_price` and `discounted_price` are NULL for **78 rows** — excluded from price/discount analysis
- `product_rating` says `'No rating available'` for **18,151 rows (90.8%)** — treated as NULL
- `crawl_timestamp` is stored as **TEXT** in PostgreSQL — must cast with `::TIMESTAMPTZ` before using `TO_CHAR()`
- `is_FK_Advantage_product` column name has **mixed case** — must always use double quotes in SQL: `"is_FK_Advantage_product"`
- `product_category_tree` contains nested bracket and quote characters — must use `REPLACE()` before `SPLIT_PART()` to extract cleanly
- `brand` has some NULL/missing values — filtered out of brand-level analysis

---

## 🛠️ Tools Used

| Tool | Purpose |
|---|---|
| Python (pandas, matplotlib, seaborn) | Data cleaning, EDA, visualisation |
| PostgreSQL | Relational database storage and SQL analysis |
| Power BI Desktop | Interactive dashboard |
| SQLAlchemy | Python → PostgreSQL data loading |

---

## 📋 Deliverables

- [x] `flipkart_com-ecommerce_sample.csv` — Raw data
- [x] `postgresql_setup.sql` — Table creation + data loading + derived columns
- [x] `flipkart_queries.sql` — 15 analytical SQL queries (PostgreSQL compatible)
- [x] `flipkart_eda.py` — Full Python EDA script
- [x] `Flipkart_Analysis_Report.docx` — Full written report
- [x] `Flipkart_Dashboard_Guide.md` — Power BI visual guide + DAX measures

---

*Dataset: Flipkart product catalogue snapshot | 20,000 products | 266 categories | 3,499 brands | Dec 2015 – Jun 2016*
