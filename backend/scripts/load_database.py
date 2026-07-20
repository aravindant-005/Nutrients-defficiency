"""
load_database.py
----------------
Processes USDA FDC and Open Food Facts datasets.
Outputs:
  - data/processed/food_database.csv  (unified food nutrient catalog)
  - Inserts records into PostgreSQL via SQLAlchemy (optional: set DB_LOAD=1)

Run:
    python scripts/load_database.py
    DB_LOAD=1 python scripts/load_database.py   (also seeds PostgreSQL)
"""
import os
import gc
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USDA_DIR = os.path.join(BASE_DIR, "data", "raw", "USDA")
OFF_DIR  = os.path.join(BASE_DIR, "data", "raw", "OpenFoodFacts")
OUT_DIR  = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

DB_LOAD = os.environ.get("DB_LOAD", "0") == "1"

# ── Target nutrients and their USDA nutrient IDs ──────────────────────────────
# Mapped from nutrient.csv (verified against the actual file)
TARGET_NUTRIENTS = {
    1008: "calories_kcal",
    1003: "protein_g",
    1005: "carbs_g",
    1004: "fat_g",
    1089: "iron_mg",
    1087: "calcium_mg",
    1114: "vitamin_d_mcg",
    1178: "vitamin_b12_mcg",
    1095: "zinc_mg",
}

# ──────────────────────────────────────────────────────────────────────────────
# 1. USDA — load food master and filter to FNDDS survey foods
# ──────────────────────────────────────────────────────────────────────────────
print("=== Loading USDA food.csv ===")
food = pd.read_csv(
    os.path.join(USDA_DIR, "food.csv"),
    usecols=["fdc_id", "description", "data_type"],
    dtype={"fdc_id": "int32"}
)
# Keep survey (FNDDS) and SR legacy food types for the most complete nutrient data
survey_types = {"survey_fndds_food", "sr_legacy_food", "foundation_food"}
food_filtered = food[food["data_type"].isin(survey_types)].copy()
valid_fdc_ids = set(food_filtered["fdc_id"].tolist())
print(f"  food.csv → {len(food_filtered)} relevant rows (FNDDS/SR/Foundation)")
del food; gc.collect()

# ──────────────────────────────────────────────────────────────────────────────
# 2. USDA — chunk-parse food_nutrient.csv and keep only target nutrients
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Processing food_nutrient.csv (chunk mode) ===")
target_ids = set(TARGET_NUTRIENTS.keys())
records = []
chunk_size = 200_000

for i, chunk in enumerate(pd.read_csv(
    os.path.join(USDA_DIR, "food_nutrient.csv"),
    usecols=["fdc_id", "nutrient_id", "amount"],
    dtype={"fdc_id": "int32", "nutrient_id": "int32", "amount": "float32"},
    chunksize=chunk_size
)):
    chunk = chunk[
        (chunk["nutrient_id"].isin(target_ids)) &
        (chunk["fdc_id"].isin(valid_fdc_ids))
    ]
    records.append(chunk)
    if (i + 1) % 25 == 0:
        print(f"  ... processed {(i+1)*chunk_size:,} rows")

nutrients_long = pd.concat(records, ignore_index=True)
print(f"  Filtered to {len(nutrients_long):,} relevant nutrient rows")
del records; gc.collect()

# ──────────────────────────────────────────────────────────────────────────────
# 3. Pivot: wide format → one row per fdc_id with nutrient columns
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Pivoting to wide format ===")
nutrients_long["nutrient_name"] = nutrients_long["nutrient_id"].map(TARGET_NUTRIENTS)
nutrients_wide = nutrients_long.pivot_table(
    index="fdc_id", columns="nutrient_name", values="amount", aggfunc="mean"
).reset_index()
nutrients_wide.columns.name = None
del nutrients_long; gc.collect()
print(f"  Pivoted shape: {nutrients_wide.shape}")

# ──────────────────────────────────────────────────────────────────────────────
# 4. Merge food descriptions with nutrient values
# ──────────────────────────────────────────────────────────────────────────────
usda_db = food_filtered.merge(nutrients_wide, on="fdc_id", how="inner")
usda_db["source"] = "USDA"
usda_db.rename(columns={"description": "food_name"}, inplace=True)
usda_db.drop(columns=["data_type"], inplace=True)
print(f"\n  USDA food_database rows: {len(usda_db)}")

# ──────────────────────────────────────────────────────────────────────────────
# 5. Open Food Facts — extract nutrient columns only
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Processing Open Food Facts ===")
SKIP_OFF = os.environ.get('SKIP_OFF', '0') == '1'
if SKIP_OFF:
    print('SKIP_OFF=1 -> skipping Open Food Facts processing to reduce memory usage')
    # Create an empty DataFrame with expected columns (will be aligned later)
    off_db = pd.DataFrame()
else:
    # Include 'countries' and keep columns needed for nutrient extraction.
    OFF_COLS = {
        "code":               "barcode",
        "product_name":       "food_name",
        "brands":             "brand",
        "countries":          "countries",
        "energy-kcal_100g":   "calories_kcal",
        "proteins_100g":      "protein_g",
        "carbohydrates_100g": "carbs_g",
        "fat_100g":           "fat_g",
        "iron_100g":          "iron_mg",
        "calcium_100g":       "calcium_mg",
        "vitamin-d_100g":     "vitamin_d_mcg",
        "vitamin-b12_100g":   "vitamin_b12_mcg",
        "zinc_100g":          "zinc_mg",
    }
    off_path = os.path.join(OFF_DIR, "en.openfoodfacts.org.products.csv.gz")

    off_chunks = []
    # Stream OFF and keep only records that are likely relevant to India
    # Filtering heuristics: product_name contains 'indian' OR countries contains 'india'
    import gzip
    import csv

    # Streaming parse to avoid pandas parser OOM on very large OFF dumps
    OFF_MAX_ROWS = int(os.environ.get("OFF_MAX_ROWS", "200000"))
    prioritized_rows = []
    other_rows = []
    seen = 0

    # Increase field size limit to handle very long OFF fields (set to 10MB)
    csv.field_size_limit(10 * 1024 * 1024)
    with gzip.open(off_path, mode="rt", encoding="utf-8", errors="replace") as fh:
        reader = csv.reader(fh, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration:
            header = []

        # Map header indices to OFF_COLS keys
        idx_map = {}
        for i, col in enumerate(header):
            if col in OFF_COLS:
                idx_map[col] = i

        # Helper to safe-get by header key
        def get_field(row, key):
            i = idx_map.get(key)
            if i is None or i >= len(row):
                return ""
            return row[i]

        for row in reader:
            seen += 1
            # extract key fields
            pname = get_field(row, "product_name").strip()
            countries = get_field(row, "countries").strip()

            lower_name = pname.lower()
            lower_ct = countries.lower()

            # check for India-related keywords
            is_india = ("indian" in lower_name) or ("india" in lower_ct)

            # check nutrient presence
            nutrient_present = False
            nutrient_vals = {}
            for off_key, mapped in OFF_COLS.items():
                if off_key in ("product_name", "code", "brands", "countries"):
                    continue
                val = get_field(row, off_key)
                if val not in (None, "", "\n"):
                    nutrient_present = True
                nutrient_vals[mapped] = val

            if is_india or nutrient_present:
                out = {
                    "barcode": get_field(row, "code"),
                    "food_name": pname,
                    "brand": get_field(row, "brands"),
                    "countries": countries,
                }
                out.update(nutrient_vals)

                if is_india:
                    prioritized_rows.append(out)
                else:
                    other_rows.append(out)

            # Stop early if we've collected enough
            if len(prioritized_rows) + len(other_rows) >= OFF_MAX_ROWS:
                # Prefer collecting a reasonable number of prioritized rows first
                if len(prioritized_rows) >= OFF_MAX_ROWS * 0.3:
                    break

    # Build DataFrame from collected rows
    if prioritized_rows or other_rows:
        # take prioritized first, then fill from others
        selected = prioritized_rows + other_rows
        selected = selected[:OFF_MAX_ROWS]
        off_db = pd.DataFrame(selected)
    else:
        off_db = pd.DataFrame()

    if off_chunks:
        off_db = pd.concat(off_chunks, ignore_index=True)
        del off_chunks; gc.collect()
    else:
        off_db = pd.DataFrame()
    if not off_db.empty:
        off_db["source"] = "OpenFoodFacts"
        off_db["fdc_id"] = None
        print(f"  Open Food Facts rows after filtering: {len(off_db)}")

        # Coerce nutrient columns to numeric where possible to avoid insertion errors
        nutrient_cols_off = [
            "calories_kcal", "protein_g", "carbohydrates", "carbs_g", "fat_g",
            "iron_mg", "calcium_mg", "vitamin_d_mcg", "vitamin_b12_mcg", "zinc_mg"
        ]
        for c in nutrient_cols_off:
            if c in off_db.columns:
                off_db[c] = pd.to_numeric(off_db[c], errors='coerce')

        # Clean product names and drop truly empty names
        off_db["food_name"] = off_db["food_name"].astype(str).str.strip()
        off_db.loc[off_db["food_name"] == "", "food_name"] = None
        off_db = off_db.dropna(subset=["food_name"], how="any")

        # Allow limiting the number of OFF rows inserted (to control DB size)
        OFF_MAX_ROWS = int(os.environ.get("OFF_MAX_ROWS", "200000"))
        if len(off_db) > OFF_MAX_ROWS:
            print(f"  OFF rows ({len(off_db):,}) exceed OFF_MAX_ROWS={OFF_MAX_ROWS}, selecting subset prioritizing India-related products")
            # Prioritize rows that mention India or 'indian' in name or countries
            mask_india = off_db["food_name"].str.contains("indian", case=False, na=False) | off_db.get("countries", "").str.contains("india", case=False, na=False)
            prioritized = off_db[mask_india].copy()
            remaining = off_db[~mask_india].copy()
            take = OFF_MAX_ROWS
            take_prior = min(len(prioritized), take)
            result_parts = []
            if take_prior > 0:
                result_parts.append(prioritized.iloc[:take_prior])
            still = take - take_prior
            if still > 0:
                # Prefer rows that have any nutrient values present
                nutrient_present = remaining[nutrient_cols_off].notna().any(axis=1)
                rem_with_nutrients = remaining[nutrient_present]
                if len(rem_with_nutrients) >= still:
                    result_parts.append(rem_with_nutrients.iloc[:still])
                else:
                    result_parts.append(rem_with_nutrients)
                    still2 = still - len(rem_with_nutrients)
                    result_parts.append(remaining.iloc[:still2])

            off_db = pd.concat(result_parts, ignore_index=True)
            print(f"  Selected {len(off_db):,} OFF rows for the dataset")

# ──────────────────────────────────────────────────────────────────────────────
# 6. Concatenate USDA + OFF into unified food_database.csv
# ──────────────────────────────────────────────────────────────────────────────
print("\n=== Building unified food_database.csv ===")
final_cols = ["fdc_id", "food_name", "source",
              "calories_kcal", "protein_g", "carbs_g", "fat_g",
              "iron_mg", "calcium_mg", "vitamin_d_mcg", "vitamin_b12_mcg", "zinc_mg"]

# Align columns for both DataFrames
for col in final_cols:
    if col not in usda_db.columns:
        usda_db[col] = None
    if col not in off_db.columns:
        off_db[col] = None

food_db = pd.concat([usda_db[final_cols], off_db[final_cols]], ignore_index=True)
food_db.reset_index(drop=True, inplace=True)


def impute_by_name_clusters(df: pd.DataFrame, nutrient_cols, n_clusters=200):
    """Impute missing nutrient values using name-based clusters.

    Approach:
    - Vectorize `food_name` via TF-IDF.
    - Cluster names (MiniBatchKMeans) to form groups of similar foods.
    - For each nutrient, fill NaNs with the cluster median for that nutrient.
    - Fall back to global median when cluster median is not available.
    """
    # Safety: require food_name column
    if "food_name" not in df.columns:
        return df

    names = df["food_name"].fillna("").astype(str)
    # If dataset is small, skip heavy processing
    if len(names) < 100:
        # simple global median imputation
        for c in nutrient_cols:
            if c in df.columns:
                df[c] = df[c].fillna(df[c].median())
        return df

    try:
        tf = TfidfVectorizer(min_df=5, max_features=20000, ngram_range=(1, 2))
        X = tf.fit_transform(names)
        # scale n_clusters with dataset size to avoid too many tiny clusters
        suggested = max(8, min(n_clusters, max(8, X.shape[0] // 50)))
        k = min(suggested, X.shape[0])
        km = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=10000)
        labels = km.fit_predict(X)
        df["_cluster"] = labels

        for col in nutrient_cols:
            if col not in df.columns:
                continue
            # cluster-level median
            med = df.groupby("_cluster")[col].median()
            df[col] = df[col].fillna(df["_cluster"].map(med))

    except Exception:
        # If clustering fails for any reason, fall back to simple median imputation
        for c in nutrient_cols:
            if c in df.columns:
                df[c] = df[c].fillna(df[c].median())

    # Global median fallback for any remaining NaNs
    for c in nutrient_cols:
        if c in df.columns:
            df[c] = df[c].fillna(df[c].median())

    if "_cluster" in df.columns:
        df.drop(columns=["_cluster"], inplace=True)

    return df

# Perform imputation for missing micronutrients using name clusters
nutrient_columns = [
    "calories_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
    "iron_mg",
    "calcium_mg",
    "vitamin_d_mcg",
    "vitamin_b12_mcg",
    "zinc_mg",
]

print('\n=== Imputing missing micronutrient values (name-cluster medians) ===')
food_db = impute_by_name_clusters(food_db, nutrient_columns, n_clusters=250)

out_path = os.path.join(OUT_DIR, "food_database.csv")
food_db.to_csv(out_path, index=False)
print(f"✓ food_database.csv saved → {len(food_db):,} rows, {food_db.shape[1]} cols")

# ──────────────────────────────────────────────────────────────────────────────
# 7. Optional: Load into PostgreSQL
# ──────────────────────────────────────────────────────────────────────────────
if DB_LOAD:
    print("\n=== Seeding PostgreSQL ===")
    from dotenv import load_dotenv
    from sqlalchemy import create_engine, text

    load_dotenv(os.path.join(BASE_DIR, ".env"))
    DB_URL = os.environ.get("DATABASE_URL")
    if not DB_URL:
        print("  ERROR: DATABASE_URL not set in .env — skipping DB load.")
    else:
        engine = create_engine(DB_URL)
        if DB_URL.startswith("sqlite"):
            # Already created by SQLAlchemy Base metadata
            pass
        else:
            with engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS food_catalog (
                        id SERIAL PRIMARY KEY,
                        fdc_id INTEGER,
                        food_name TEXT NOT NULL,
                        source VARCHAR(50),
                        calories_kcal FLOAT,
                        protein_g FLOAT,
                        carbs_g FLOAT,
                        fat_g FLOAT,
                        iron_mg FLOAT,
                        calcium_mg FLOAT,
                        vitamin_d_mcg FLOAT,
                        vitamin_b12_mcg FLOAT,
                        zinc_mg FLOAT
                    );
                """))

        # Insert in chunks to avoid memory issues
        chunk_size = 10_000
        for start in range(0, len(food_db), chunk_size):
            batch = food_db.iloc[start:start + chunk_size]
            batch.to_sql("food_catalog", engine, if_exists="append", index=False)
            print(f"  Inserted rows {start}–{start + len(batch)}")

        print(f"✓ PostgreSQL seeded with {len(food_db):,} food records.")
