# ============================================================
# FLIPKART E-COMMERCE DATA ANALYSIS — FULL EDA
# ============================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

sns.set_theme(style="darkgrid")
plt.rcParams.update({'figure.dpi': 120, 'figure.figsize': (12, 6)})
PALETTE = "Set2"

# ============================================================
# 1. LOAD DATA
# ============================================================
df = pd.read_csv("D:/flipkart_com-ecommerce_sample.csv")
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print()
print("Sample:")
print(df[['product_name','retail_price','discounted_price','brand','product_rating']].head())

# ============================================================
# 2. DATA CLEANING & FEATURE ENGINEERING
# ============================================================

# 2a. Extract main category (first item in category tree)
df['main_category'] = df['product_category_tree'].str.extract(r'"([^">>]+)')

# 2b. Extract sub-category (second item)
df['sub_category'] = df['product_category_tree'].str.extract(r'>> ([^>>]+) >>')

# 2c. Clean ratings — strip "No rating available"
df['rating'] = pd.to_numeric(
    df['product_rating'].str.extract(r'(\d+\.?\d*)')[0], errors='coerce'
)

# 2d. Discount % and savings
df['discount_pct']  = ((df['retail_price'] - df['discounted_price']) /
                        df['retail_price'] * 100).round(2)
df['savings_amt']   = (df['retail_price'] - df['discounted_price']).round(2)

# 2e. Price bucket
df['price_bucket'] = pd.cut(
    df['discounted_price'],
    bins=[0, 500, 1000, 2000, 5000, 10000, 1e7],
    labels=['₹0–500', '₹501–1K', '₹1K–2K', '₹2K–5K', '₹5K–10K', '₹10K+']
)

# 2f. Crawl date
df['crawl_date'] = pd.to_datetime(df['crawl_timestamp'].str[:10])

# 2g. Has rating flag
df['has_rating'] = df['rating'].notna()

print("\nCleaned DataFrame info:")
print(df[['main_category','discount_pct','savings_amt','rating','price_bucket']].describe(include='all'))

print("\nNull counts after cleaning:")
print(df[['retail_price','discounted_price','brand','rating','main_category']].isnull().sum())

from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:aryan@localhost:5432/postgres')
# Store DataFrame to SQL table
df.to_sql(
    name='flipkart',        # Table name
    con=engine,             # Database connection
    if_exists='replace',    # Options: 'fail', 'replace', 'append'
    index=False             # Don't write DataFrame index as a column
)

# ============================================================
# 3. UNIVARIATE ANALYSIS
# ============================================================

# -- 3a. Products per category --------------------------------
top_cats = df['main_category'].value_counts().head(15).reset_index()
top_cats.columns = ['category', 'count']
plt.figure(figsize=(12, 7))
sns.barplot(data=top_cats, x='count', y='category', palette='Blues_r')
plt.title('Top 15 Product Categories by Listing Count', fontsize=14)
plt.xlabel('Number of Products'); plt.ylabel('Category')
plt.tight_layout(); plt.savefig('cat_product_count.png'); plt.close()

# -- 3b. Price distribution (log scale) ----------------------
plt.figure()
sns.histplot(df['discounted_price'].dropna(), bins=60, color='steelblue', log_scale=(True, False))
plt.title('Distribution of Discounted Prices (Log Scale)')
plt.xlabel('Discounted Price (₹)'); plt.ylabel('Count')
plt.tight_layout(); plt.savefig('price_distribution.png'); plt.close()

# -- 3c. Discount % distribution ------------------------------
plt.figure()
sns.histplot(df['discount_pct'].dropna(), bins=50, color='tomato', kde=True)
plt.title('Distribution of Discount Percentages')
plt.xlabel('Discount %'); plt.ylabel('Count')
plt.tight_layout(); plt.savefig('discount_distribution.png'); plt.close()

# -- 3d. Rating distribution ----------------------------------
plt.figure(figsize=(8, 5))
df['rating'].dropna().value_counts().sort_index().plot.bar(color=sns.color_palette(PALETTE))
plt.title('Product Rating Distribution (1–5)')
plt.xlabel('Rating'); plt.ylabel('Count')
plt.tight_layout(); plt.savefig('rating_distribution.png'); plt.close()

# -- 3e. Price bucket share -----------------------------------
bucket_counts = df['price_bucket'].value_counts().sort_index().reset_index()
bucket_counts.columns = ['price_bucket', 'count']
plt.figure(figsize=(9, 5))
sns.barplot(data=bucket_counts, x='price_bucket', y='count', palette='YlOrRd')
plt.title('Products by Price Bucket')
plt.xlabel('Price Range (₹)'); plt.ylabel('Count')
plt.tight_layout(); plt.savefig('price_bucket.png'); plt.close()

# -- 3f. FK Advantage pie ------------------------------------
fk_counts = df['is_FK_Advantage_product'].value_counts()
plt.figure(figsize=(6, 6))
plt.pie(fk_counts, labels=['Regular', 'FK Advantage'],
        autopct='%1.1f%%', startangle=90, colors=['#4e79a7','#f28e2b'])
plt.title('FK Advantage vs Regular Products')
plt.tight_layout(); plt.savefig('fk_advantage_pie.png'); plt.close()

# ============================================================
# 4. CATEGORY ANALYSIS
# ============================================================

# -- 4a. Avg discounted price per top category ---------------
cat_price = (df[df['main_category'].isin(top_cats['category'])]
             .groupby('main_category')['discounted_price']
             .mean().sort_values(ascending=False).reset_index())
cat_price.columns = ['category', 'avg_price']
plt.figure(figsize=(12, 7))
sns.barplot(data=cat_price, x='avg_price', y='category', palette='coolwarm')
plt.title('Average Discounted Price per Category')
plt.xlabel('Avg Price (₹)'); plt.ylabel('Category')
plt.tight_layout(); plt.savefig('cat_avg_price.png'); plt.close()

# -- 4b. Avg discount % per category -------------------------
cat_disc = (df[df['main_category'].isin(top_cats['category'])]
            .groupby('main_category')['discount_pct']
            .mean().sort_values(ascending=False).reset_index())
cat_disc.columns = ['category', 'avg_discount']
plt.figure(figsize=(12, 7))
sns.barplot(data=cat_disc, x='avg_discount', y='category', palette='RdYlGn_r')
plt.title('Average Discount % per Category')
plt.xlabel('Avg Discount %'); plt.ylabel('Category')
plt.tight_layout(); plt.savefig('cat_avg_discount.png'); plt.close()

# -- 4c. Avg rating per category (min 50 products) -----------
cat_rating = (df.groupby('main_category')
              .agg(count=('rating','count'), avg_rating=('rating','mean'))
              .reset_index())
cat_rating = cat_rating[cat_rating['count'] >= 50].sort_values('avg_rating', ascending=False)
plt.figure(figsize=(10, 6))
sns.barplot(data=cat_rating, x='avg_rating', y='main_category', palette='Blues_r')
plt.title('Average Rating per Category (min 50 rated products)')
plt.xlabel('Avg Rating'); plt.ylabel('Category')
plt.xlim(0, 5); plt.tight_layout(); plt.savefig('cat_avg_rating.png'); plt.close()

# ============================================================
# 5. BRAND ANALYSIS
# ============================================================

# -- 5a. Top 20 brands by listing count ----------------------
top_brands = df['brand'].value_counts().head(20).reset_index()
top_brands.columns = ['brand', 'count']
plt.figure(figsize=(12, 7))
sns.barplot(data=top_brands, x='count', y='brand', palette='Purples_r')
plt.title('Top 20 Brands by Product Listings')
plt.xlabel('Listings'); plt.ylabel('Brand')
plt.tight_layout(); plt.savefig('top_brands.png'); plt.close()

# -- 5b. Top brands by avg discount (min 30 products) --------
brand_disc = (df.groupby('brand')
              .agg(count=('discount_pct','count'), avg_disc=('discount_pct','mean'))
              .reset_index())
brand_disc = brand_disc[brand_disc['count'] >= 30].sort_values('avg_disc', ascending=False).head(15)
plt.figure(figsize=(12, 7))
sns.barplot(data=brand_disc, x='avg_disc', y='brand', palette='Oranges_r')
plt.title('Top 15 Brands by Avg Discount % (min 30 products)')
plt.xlabel('Avg Discount %'); plt.ylabel('Brand')
plt.tight_layout(); plt.savefig('brand_avg_discount.png'); plt.close()

# -- 5c. Top brands by avg rating (min 30 products) ----------
brand_rating = (df.groupby('brand')
                .agg(count=('rating','count'), avg_rating=('rating','mean'))
                .reset_index())
brand_rating = brand_rating[brand_rating['count'] >= 30].sort_values('avg_rating', ascending=False).head(15)
print("\nTop Brands by Avg Rating:")
print(brand_rating)

# ============================================================
# 6. PRICING & DISCOUNT DEEP DIVE
# ============================================================

# -- 6a. Scatter: retail price vs discount % -----------------
sample = df.dropna(subset=['retail_price','discount_pct']).sample(3000, random_state=42)
plt.figure()
sns.scatterplot(data=sample, x='retail_price', y='discount_pct',
                hue='main_category', alpha=0.5, s=30, legend=False)
plt.xscale('log')
plt.title('Retail Price vs Discount % (log scale, sample of 3000)')
plt.xlabel('Retail Price (₹, log)'); plt.ylabel('Discount %')
plt.tight_layout(); plt.savefig('price_vs_discount_scatter.png'); plt.close()

# -- 6b. Top 10 products by absolute savings -----------------
top_savings = df.nlargest(10, 'savings_amt')[['product_name','retail_price','discounted_price','savings_amt','main_category']]
print("\nTop 10 Products by Absolute Savings (₹):")
print(top_savings.to_string())

# -- 6c. Zero discount vs heavy discount breakdown -----------
disc_summary = pd.DataFrame({
    'Segment': ['0% discount', '1–25%', '26–50%', '51–75%', '>75%'],
    'Count': [
        (df['discount_pct'] == 0).sum(),
        df['discount_pct'].between(1, 25).sum(),
        df['discount_pct'].between(26, 50).sum(),
        df['discount_pct'].between(51, 75).sum(),
        (df['discount_pct'] > 75).sum(),
    ]
})
print("\nDiscount Segment Breakdown:")
print(disc_summary)
plt.figure(figsize=(9, 5))
sns.barplot(data=disc_summary, x='Segment', y='Count', palette='Set1')
plt.title('Products by Discount Segment')
plt.tight_layout(); plt.savefig('discount_segments.png'); plt.close()

# ============================================================
# 7. FK ADVANTAGE ANALYSIS
# ============================================================
fk_compare = df.groupby('is_FK_Advantage_product').agg(
    avg_retail_price   = ('retail_price',    'mean'),
    avg_disc_price     = ('discounted_price', 'mean'),
    avg_discount_pct   = ('discount_pct',     'mean'),
    avg_rating         = ('rating',           'mean'),
    total_products     = ('uniq_id',          'count')
).round(2)
print("\nFK Advantage vs Regular Product Comparison:")
print(fk_compare)

fk_cats = df[df['is_FK_Advantage_product'] == True]['main_category'].value_counts().head(10).reset_index()
fk_cats.columns = ['category', 'fk_count']
plt.figure(figsize=(10, 6))
sns.barplot(data=fk_cats, x='fk_count', y='category', palette='Set2')
plt.title('Top Categories for FK Advantage Products')
plt.xlabel('FK Advantage Products'); plt.ylabel('Category')
plt.tight_layout(); plt.savefig('fk_advantage_categories.png'); plt.close()

# ============================================================
# 8. RATING ANALYSIS
# ============================================================

# -- 8a. Rating vs price bucket box plot ---------------------
rated = df.dropna(subset=['rating','price_bucket'])
plt.figure(figsize=(11, 6))
sns.boxplot(data=rated, x='price_bucket', y='rating', palette=PALETTE)
plt.title('Product Rating Distribution by Price Bucket')
plt.xlabel('Price Bucket'); plt.ylabel('Rating')
plt.tight_layout(); plt.savefig('rating_by_price_bucket.png'); plt.close()

# -- 8b. % products with ratings per category ----------------
has_rating_pct = (df.groupby('main_category')['has_rating']
                  .mean().mul(100).sort_values(ascending=False)
                  .reset_index())
has_rating_pct.columns = ['category', 'pct_rated']
print("\n% Products with Ratings per Category (top 10):")
print(has_rating_pct.head(10))

# ============================================================
# 9. TIME SERIES (CRAWL DATE ANALYSIS)
# ============================================================
crawl_trend = df.groupby('crawl_date')['uniq_id'].count().reset_index()
crawl_trend.columns = ['date', 'products_crawled']
plt.figure()
sns.lineplot(data=crawl_trend, x='date', y='products_crawled', color='darkblue')
plt.title('Products Crawled per Day Over Time')
plt.xlabel('Date'); plt.ylabel('Products Crawled')
plt.xticks(rotation=45); plt.tight_layout()
plt.savefig('crawl_trend.png'); plt.close()

print("\n✅ All charts saved. EDA complete!")
```