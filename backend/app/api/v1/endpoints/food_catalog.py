"""
food_catalog.py — GET /api/v1/food-catalog/search
Searches the PostgreSQL food nutrition catalog with autocomplete support.
Falls back to a curated static list if the database is not yet seeded.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.deficiency import FoodCatalog, User
from app.schemas.food_log import FoodCatalogOut

router = APIRouter()

# Curated Indian + global high-quality fallback catalog (per 100g)
FALLBACK_FOODS = [
    # Indian foods
    {"id": 9001, "food_name": "Spinach (Palak), raw", "calories_kcal": 23.0, "protein_g": 2.86, "carbs_g": 3.63, "fat_g": 0.39, "iron_mg": 2.71, "calcium_mg": 99.0, "magnesium_mg": 79.0, "vitamin_c_mg": 28.1, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.53, "source": "USDA", "cuisine_type": "Indian"},
    {"id": 9002, "food_name": "Dal (Lentils), cooked", "calories_kcal": 116.0, "protein_g": 9.02, "carbs_g": 20.13, "fat_g": 0.38, "iron_mg": 3.33, "calcium_mg": 19.0, "magnesium_mg": 36.0, "vitamin_c_mg": 1.5, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 1.27, "source": "IFCT", "cuisine_type": "Indian"},
    {"id": 9003, "food_name": "Paneer (Cottage Cheese)", "calories_kcal": 265.0, "protein_g": 18.3, "carbs_g": 1.2, "fat_g": 20.8, "iron_mg": 0.2, "calcium_mg": 480.0, "magnesium_mg": 15.0, "vitamin_c_mg": 0.0, "vitamin_d_mcg": 0.3, "vitamin_b12_mcg": 0.6, "zinc_mg": 2.7, "source": "IFCT", "cuisine_type": "Indian"},
    {"id": 9004, "food_name": "Amla (Indian Gooseberry)", "calories_kcal": 44.0, "protein_g": 0.9, "carbs_g": 10.2, "fat_g": 0.6, "iron_mg": 1.2, "calcium_mg": 25.0, "magnesium_mg": 10.0, "vitamin_c_mg": 600.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.12, "source": "IFCT", "cuisine_type": "Indian"},
    {"id": 9005, "food_name": "Guava", "calories_kcal": 68.0, "protein_g": 2.55, "carbs_g": 14.3, "fat_g": 0.95, "iron_mg": 0.26, "calcium_mg": 18.0, "magnesium_mg": 22.0, "vitamin_c_mg": 228.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.23, "source": "USDA", "cuisine_type": "Indian"},
    {"id": 9006, "food_name": "Sesame Seeds (Til)", "calories_kcal": 573.0, "protein_g": 17.7, "carbs_g": 23.5, "fat_g": 49.7, "iron_mg": 14.6, "calcium_mg": 975.0, "magnesium_mg": 351.0, "vitamin_c_mg": 0.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 7.75, "source": "IFCT", "cuisine_type": "Indian"},
    {"id": 9007, "food_name": "Dates (Khajoor)", "calories_kcal": 277.0, "protein_g": 1.81, "carbs_g": 75.0, "fat_g": 0.15, "iron_mg": 0.9, "calcium_mg": 64.0, "magnesium_mg": 54.0, "vitamin_c_mg": 0.4, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.44, "source": "USDA", "cuisine_type": "Indian"},
    {"id": 9008, "food_name": "Beetroot, cooked", "calories_kcal": 44.0, "protein_g": 1.68, "carbs_g": 10.0, "fat_g": 0.18, "iron_mg": 0.79, "calcium_mg": 16.0, "magnesium_mg": 23.0, "vitamin_c_mg": 3.6, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.35, "source": "USDA", "cuisine_type": "Indian"},
    {"id": 9009, "food_name": "Curd (Yogurt)", "calories_kcal": 98.0, "protein_g": 3.5, "carbs_g": 3.4, "fat_g": 6.0, "iron_mg": 0.14, "calcium_mg": 110.0, "magnesium_mg": 12.0, "vitamin_c_mg": 0.5, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.4, "zinc_mg": 0.52, "source": "IFCT", "cuisine_type": "Indian"},
    {"id": 9010, "food_name": "Chicken (Breast), cooked", "calories_kcal": 165.0, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6, "iron_mg": 0.89, "calcium_mg": 15.0, "magnesium_mg": 29.0, "vitamin_c_mg": 0.0, "vitamin_d_mcg": 0.1, "vitamin_b12_mcg": 0.31, "zinc_mg": 1.0, "source": "USDA", "cuisine_type": "Indian"},
    {"id": 9011, "food_name": "Eggs, whole, cooked", "calories_kcal": 155.0, "protein_g": 12.6, "carbs_g": 1.12, "fat_g": 10.6, "iron_mg": 1.75, "calcium_mg": 50.0, "magnesium_mg": 12.0, "vitamin_c_mg": 0.0, "vitamin_d_mcg": 2.0, "vitamin_b12_mcg": 1.11, "zinc_mg": 1.29, "source": "USDA", "cuisine_type": "Global"},
    {"id": 9012, "food_name": "Milk, full fat", "calories_kcal": 61.0, "protein_g": 3.2, "carbs_g": 4.8, "fat_g": 3.3, "iron_mg": 0.03, "calcium_mg": 113.0, "magnesium_mg": 11.0, "vitamin_c_mg": 0.9, "vitamin_d_mcg": 1.3, "vitamin_b12_mcg": 0.45, "zinc_mg": 0.38, "source": "IFCT", "cuisine_type": "Global"},
    # Western / Global
    {"id": 9013, "food_name": "Salmon, wild, cooked", "calories_kcal": 182.0, "protein_g": 25.0, "carbs_g": 0.0, "fat_g": 8.0, "iron_mg": 0.8, "calcium_mg": 12.0, "magnesium_mg": 29.0, "vitamin_c_mg": 3.9, "vitamin_d_mcg": 10.9, "vitamin_b12_mcg": 4.8, "zinc_mg": 0.6, "source": "USDA", "cuisine_type": "Western"},
    {"id": 9014, "food_name": "Beef Liver, cooked", "calories_kcal": 175.0, "protein_g": 26.4, "carbs_g": 4.5, "fat_g": 4.9, "iron_mg": 6.18, "calcium_mg": 5.0, "magnesium_mg": 18.0, "vitamin_c_mg": 1.3, "vitamin_d_mcg": 1.2, "vitamin_b12_mcg": 59.3, "zinc_mg": 4.44, "source": "USDA", "cuisine_type": "Western"},
    {"id": 9015, "food_name": "Almonds", "calories_kcal": 579.0, "protein_g": 21.2, "carbs_g": 21.6, "fat_g": 49.9, "iron_mg": 3.71, "calcium_mg": 264.0, "magnesium_mg": 270.0, "vitamin_c_mg": 0.0, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 3.12, "source": "USDA", "cuisine_type": "Global"},
    {"id": 9016, "food_name": "Pumpkin Seeds", "calories_kcal": 559.0, "protein_g": 30.2, "carbs_g": 10.7, "fat_g": 49.1, "iron_mg": 8.82, "calcium_mg": 46.0, "magnesium_mg": 592.0, "vitamin_c_mg": 1.9, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 7.81, "source": "USDA", "cuisine_type": "Global"},
    {"id": 9017, "food_name": "Orange", "calories_kcal": 47.0, "protein_g": 0.94, "carbs_g": 11.8, "fat_g": 0.12, "iron_mg": 0.1, "calcium_mg": 40.0, "magnesium_mg": 10.0, "vitamin_c_mg": 53.2, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.07, "source": "USDA", "cuisine_type": "Global"},
    {"id": 9018, "food_name": "Tuna, canned in water", "calories_kcal": 116.0, "protein_g": 25.5, "carbs_g": 0.0, "fat_g": 0.82, "iron_mg": 1.02, "calcium_mg": 11.0, "magnesium_mg": 31.0, "vitamin_c_mg": 0.0, "vitamin_d_mcg": 5.4, "vitamin_b12_mcg": 2.2, "zinc_mg": 0.9, "source": "USDA", "cuisine_type": "Global"},
    {"id": 9019, "food_name": "Tofu, firm", "calories_kcal": 76.0, "protein_g": 8.08, "carbs_g": 1.87, "fat_g": 4.78, "iron_mg": 1.61, "calcium_mg": 350.0, "magnesium_mg": 30.0, "vitamin_c_mg": 0.1, "vitamin_d_mcg": 0.0, "vitamin_b12_mcg": 0.0, "zinc_mg": 0.8, "source": "USDA", "cuisine_type": "Global"},
    {"id": 9020, "food_name": "Oysters, cooked", "calories_kcal": 163.0, "protein_g": 19.0, "carbs_g": 10.0, "fat_g": 5.0, "iron_mg": 9.2, "calcium_mg": 62.0, "magnesium_mg": 47.0, "vitamin_c_mg": 4.7, "vitamin_d_mcg": 8.0, "vitamin_b12_mcg": 16.0, "zinc_mg": 16.6, "source": "USDA", "cuisine_type": "Western"},
]


@router.get("/search", response_model=List[FoodCatalogOut])
def search_food_catalog(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(20, ge=1, le=50),
    cuisine_type: Optional[str] = Query(None, description="Filter by cuisine: Indian / Western / Global"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search the food nutrition catalog by name with autocomplete.
    Returns results from PostgreSQL database; falls back to curated static list if DB is empty.
    Supports optional cuisine type filter (Indian / Western / Global).
    """
    query = (
        db.query(FoodCatalog)
        .filter(FoodCatalog.food_name.ilike(f"%{q}%"))
    )
    if cuisine_type:
        query = query.filter(FoodCatalog.cuisine_type == cuisine_type)

    results = query.limit(limit).all()

    if not results:
        q_lower = q.lower()
        filtered = [
            item for item in FALLBACK_FOODS
            if q_lower in item["food_name"].lower()
            and (not cuisine_type or item.get("cuisine_type") == cuisine_type)
        ]
        return [FoodCatalogOut(**item) for item in filtered[:limit]]

    return results
