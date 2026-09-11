import os
import pandas as pd
import logging

logger = logging.getLogger("indb_service")
INDB_PATH = "dataset/Indian-Nutrient-Databank-INDB--main/INDB.xlsx"

NON_VEG_KEYWORDS = ["chicken", "mutton", "egg", "fish", "meat", "pork", "beef", "liver", "prawn", "seafood", "halibut", "salmon"]
DAIRY_KEYWORDS = ["milk", "curd", "paneer", "ghee", "butter", "cheese", "yogurt", "yoghurt", "dahi"]

class INDBService:
    def __init__(self):
        self.df = None
        self.load_dataset()

    def load_dataset(self):
        if not os.path.exists(INDB_PATH):
            logger.error(f"INDB dataset not found at {INDB_PATH}")
            return
        
        try:
            df = pd.read_excel(INDB_PATH)
            numeric_cols = [
                'energy_kcal', 'protein_g', 'carb_g', 'fat_g', 'fibre_g',
                'iron_mg', 'calcium_mg', 'vitd2_ug', 'vitd3_ug', 'zinc_mg',
                'magnesium_mg', 'vitc_mg', 'folate_ug', 'vitb12_ug'
            ]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                else:
                    df[col] = 0.0

            df['vitamin_d_mcg'] = df['vitd2_ug'] + df['vitd3_ug']
            df['food_name'] = df['food_name'].astype(str).str.strip()
            self.df = df
            logger.info(f"Loaded INDB Indian Food Databank with {len(df)} records.")
        except Exception as e:
            logger.error(f"Error loading INDB excel dataset: {e}")

    def search_foods(self, query: str = "", limit: int = 20):
        if self.df is None or self.df.empty:
            return []
        
        if not query or query.strip() == "":
            sample = self.df.head(limit)
        else:
            q = query.lower().strip()
            mask = self.df['food_name'].str.lower().str.contains(q, na=False)
            sample = self.df[mask].head(limit)

        results = []
        for _, row in sample.iterrows():
            results.append({
                "food_code": str(row.get('food_code', '')),
                "food_name": str(row.get('food_name', '')),
                "serving_unit": str(row.get('servings_unit', '100g serving')),
                "calories_kcal": float(row.get('energy_kcal', 0.0)),
                "protein_g": float(row.get('protein_g', 0.0)),
                "carbs_g": float(row.get('carb_g', 0.0)),
                "fat_g": float(row.get('fat_g', 0.0)),
                "fiber_g": float(row.get('fibre_g', 0.0)),
                "iron_mg": float(row.get('iron_mg', 0.0)),
                "calcium_mg": float(row.get('calcium_mg', 0.0)),
                "vitamin_d_mcg": float(row.get('vitamin_d_mcg', 0.0)),
                "vitamin_b12_mcg": float(row.get('vitb12_ug', 0.0)),
                "zinc_mg": float(row.get('zinc_mg', 0.0)),
                "magnesium_mg": float(row.get('magnesium_mg', 0.0)),
                "vitamin_c_mg": float(row.get('vitc_mg', 0.0))
            })
        return results

    def get_top_foods_for_nutrient(self, nutrient: str, diet_type: str = "Vegetarian", top_n: int = 5):
        if self.df is None or self.df.empty:
            return ["Nutritious Indian Whole Foods", "Spinach/Leafy Greens", "Lentils/Dal", "Dairy", "Nuts & Seeds"]

        nutrient_col_map = {
            "iron": "iron_mg",
            "calcium": "calcium_mg",
            "vitamin_d": "vitamin_d_mcg",
            "vitamin_b12": "vitb12_ug",
            "zinc": "zinc_mg",
            "magnesium": "magnesium_mg",
            "vitamin_c": "vitc_mg"
        }

        col = nutrient_col_map.get(nutrient.lower())

        # Filter dataset based on diet preference
        filtered_df = self.df.copy()
        diet = (diet_type or "Vegetarian").lower()

        if "veg" in diet and "non" not in diet:
            # Exclude non-vegetarian items
            pattern = "|".join(NON_VEG_KEYWORDS)
            filtered_df = filtered_df[~filtered_df['food_name'].str.lower().str.contains(pattern, na=False)]

        if "vegan" in diet:
            # Exclude dairy + non-veg
            pattern = "|".join(NON_VEG_KEYWORDS + DAIRY_KEYWORDS)
            filtered_df = filtered_df[~filtered_df['food_name'].str.lower().str.contains(pattern, na=False)]

        if not col or col not in filtered_df.columns or filtered_df[col].max() == 0:
            fallbacks = {
                "iron": ["Kamal Kakdi (Lotus Stem)", "Spinach (Palak)", "Jaggery (Gur)", "Garden Cress Seeds", "Bengal Gram"],
                "calcium": ["Ragi (Finger Millet)", "Sesame Seeds (Til)", "Milk & Paneer", "Amaranth Leaves", "Curd"],
                "vitamin_d": ["Fortified Milk", "Egg Yolk", "Mushrooms exposed to UV", "Fortified Oil", "Fatty Fish"],
                "vitamin_b12": ["Milk & Curd", "Paneer", "Fortified Cereals", "Curd / Dahi", "Fortified Soy Milk"],
                "zinc": ["Pumpkin Seeds", "Cashews", "Chickpeas (Chana)", "Whole Wheat Roti", "Lentils (Dal)"],
                "magnesium": ["Almonds & Cashews", "Spinach (Palak)", "Whole Wheat", "Black Beans", "Dark Chocolate"],
                "vitamin_c": ["Amla (Indian Gooseberry)", "Guava (Amrood)", "Capsicum", "Lemon/Lime Juice", "Drumstick Leaves"]
            }
            return fallbacks.get(nutrient.lower(), ["Balanced Indian Diet"])

        top_rows = filtered_df.sort_values(by=col, ascending=False).head(top_n)
        return top_rows['food_name'].tolist()

indb_service = INDBService()
