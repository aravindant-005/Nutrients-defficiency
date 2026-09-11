"""
recommendation_service.py
--------------------------
Generates personalized food recommendations, health advice, and weekly meal plans
based on predicted deficiency risks for all 7 micronutrient targets.

Features:
  - Indian + global food recommendations with vegetarian/non-veg categorisation
  - RDA-based nutrient targets (adjusted for age and gender per ICMR/WHO guidelines)
  - Weekly 7-day meal plan generation
  - Foods to avoid for each deficiency
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.deficiency import FoodCatalog, User
from app.schemas.predict import (
    RecommendationFoodItem, NutrientTarget, RecommendationsOut, DayMealPlan
)

# ── Static food recommendations (per 100g, Indian-first) ─────────────────────

STATIC_FOODS = {
    "iron": [
        {"food_name": "Spinach (Palak)", "amount": 2.71, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Dal palak for lunch"},
        {"food_name": "Masoor Dal (Red Lentils)", "amount": 7.58, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Dal with rice for dinner"},
        {"food_name": "Dates (Khajoor)", "amount": 0.90, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Dates as morning snack"},
        {"food_name": "Sesame Seeds (Til)", "amount": 14.6, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Til chikki as snack"},
        {"food_name": "Beetroot", "amount": 0.79, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Beetroot salad or sabzi"},
        {"food_name": "Beef Liver", "amount": 6.18, "unit": "mg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Liver fry with rice"},
        {"food_name": "Pumpkin Seeds", "amount": 8.82, "unit": "mg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Sprinkle on salads"},
    ],
    "calcium": [
        {"food_name": "Paneer (Cottage Cheese)", "amount": 480.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Palak paneer for dinner"},
        {"food_name": "Curd (Yogurt)", "amount": 110.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Curd rice or raita"},
        {"food_name": "Sesame Seeds (Til)", "amount": 975.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Til ladoo as snack"},
        {"food_name": "Milk", "amount": 113.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Glass of warm milk at night"},
        {"food_name": "Sardines (canned)", "amount": 380.0, "unit": "mg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Sardine curry"},
        {"food_name": "Almonds", "amount": 264.0, "unit": "mg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Soaked almonds for breakfast"},
        {"food_name": "Tofu (calcium-set)", "amount": 350.0, "unit": "mg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Tofu stir fry"},
    ],
    "vitamin_d": [
        {"food_name": "Eggs (whole)", "amount": 2.0, "unit": "mcg", "is_vegetarian": False, "is_indian": True,  "meal_suggestion": "Egg omelette for breakfast"},
        {"food_name": "Milk (fortified)", "amount": 1.3, "unit": "mcg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Glass of milk with turmeric"},
        {"food_name": "Wild-caught Salmon", "amount": 10.9, "unit": "mcg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Grilled salmon for dinner"},
        {"food_name": "Canned Tuna", "amount": 5.4, "unit": "mcg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Tuna sandwich for lunch"},
        {"food_name": "Egg Yolks", "amount": 5.4, "unit": "mcg", "is_vegetarian": False, "is_indian": True,  "meal_suggestion": "Boiled eggs as snack"},
        {"food_name": "Oysters", "amount": 8.0, "unit": "mcg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Oyster curry"},
        {"food_name": "Mushrooms (UV-exposed)", "amount": 3.0, "unit": "mcg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Mushroom masala"},
    ],
    "vitamin_b12": [
        {"food_name": "Chicken Liver", "amount": 18.0, "unit": "mcg", "is_vegetarian": False, "is_indian": True,  "meal_suggestion": "Chicken liver curry"},
        {"food_name": "Eggs", "amount": 1.11, "unit": "mcg", "is_vegetarian": False, "is_indian": True,  "meal_suggestion": "Egg bhurji for breakfast"},
        {"food_name": "Milk", "amount": 0.45, "unit": "mcg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Daily milk intake"},
        {"food_name": "Curd (Yogurt)", "amount": 0.4, "unit": "mcg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Curd with every meal"},
        {"food_name": "Fish (Rohu/Catla)", "amount": 2.4, "unit": "mcg", "is_vegetarian": False, "is_indian": True,  "meal_suggestion": "Fish curry with rice"},
        {"food_name": "Beef Liver", "amount": 59.3, "unit": "mcg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Liver fry"},
        {"food_name": "Fortified Nutritional Yeast", "amount": 49.0, "unit": "mcg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Sprinkle on food"},
    ],
    "zinc": [
        {"food_name": "Pumpkin Seeds", "amount": 7.81, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Roasted pumpkin seeds as snack"},
        {"food_name": "Sesame Seeds (Til)", "amount": 7.75, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Til ke ladoo"},
        {"food_name": "Chickpeas (Chana)", "amount": 2.76, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Chana masala for lunch"},
        {"food_name": "Paneer", "amount": 2.7,  "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Paneer tikka"},
        {"food_name": "Beef (lean)", "amount": 6.3,  "unit": "mg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Beef curry"},
        {"food_name": "Oysters", "amount": 16.6, "unit": "mg", "is_vegetarian": False, "is_indian": False, "meal_suggestion": "Oyster fry"},
        {"food_name": "Cashews", "amount": 5.78, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Kaju katli as snack"},
    ],
    "magnesium": [
        {"food_name": "Pumpkin Seeds", "amount": 592.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Add to trail mix"},
        {"food_name": "Almonds", "amount": 270.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "10 soaked almonds daily"},
        {"food_name": "Black Beans (Kala Chana)", "amount": 70.0,  "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Kala chana chaat"},
        {"food_name": "Spinach (Palak)", "amount": 79.0,  "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Palak soup"},
        {"food_name": "Banana", "amount": 27.0,  "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Mid-morning banana"},
        {"food_name": "Dark Chocolate (70%+)", "amount": 228.0, "unit": "mg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Small square after dinner"},
        {"food_name": "Avocado", "amount": 29.0,  "unit": "mg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Avocado toast"},
    ],
    "vitamin_c": [
        {"food_name": "Amla (Indian Gooseberry)", "amount": 600.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Amla juice every morning"},
        {"food_name": "Guava", "amount": 228.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Guava as afternoon snack"},
        {"food_name": "Lemon", "amount": 53.0,  "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Lemon water with meals"},
        {"food_name": "Orange", "amount": 53.2,  "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Orange as mid-morning snack"},
        {"food_name": "Bell Peppers (Capsicum)", "amount": 128.0, "unit": "mg", "is_vegetarian": True,  "is_indian": True,  "meal_suggestion": "Add to sabzi or salad"},
        {"food_name": "Strawberries", "amount": 58.8,  "unit": "mg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Strawberry smoothie"},
        {"food_name": "Kiwi", "amount": 92.7,  "unit": "mg", "is_vegetarian": True,  "is_indian": False, "meal_suggestion": "Kiwi fruit salad"},
    ],
}

FOODS_TO_AVOID = {
    "iron":        "Avoid tea, coffee, and calcium supplements with iron-rich meals (block absorption). Avoid phytate-rich foods (unsoaked raw grains) with iron sources.",
    "calcium":     "Avoid excess sodium and phosphoric acid (dark sodas/colas) — they increase urinary calcium loss. Limit oxalate-rich foods (spinach, rhubarb) in large amounts.",
    "vitamin_d":   "Avoid excessive alcohol — impairs liver conversion of Vitamin D to its active form. Avoid staying indoors all day; 15 min of sunlight is beneficial.",
    "vitamin_b12": "Avoid heavy alcohol intake. If vegan, strictly supplement B12 — it is absent in plant foods. Avoid mega-dose Vitamin C supplements at meal time (destroys B12).",
    "zinc":        "Avoid unsoaked legumes and whole grains with zinc-rich foods (phytates bind zinc). Avoid excess iron supplementation — competes with zinc absorption.",
    "magnesium":   "Avoid excess refined sugar, alcohol, and caffeine — all increase urinary magnesium excretion. Avoid cooking vegetables in excess water (leaches magnesium).",
    "vitamin_c":   "Avoid cooking at very high temperatures (destroys Vitamin C). Avoid storing cut fruits/vegetables for too long. Smoking significantly depletes Vitamin C levels.",
}

HEALTH_ADVICE = {
    "iron":        "Combine iron-rich foods (dal, spinach) with Vitamin C sources (lemon juice, amla) to boost non-heme iron absorption by up to 3×.",
    "calcium":     "Pair calcium-rich foods with Vitamin D (sunlight or eggs) for optimal absorption. Aim for 1000–1200 mg calcium daily through diet.",
    "vitamin_d":   "Get 15–20 minutes of morning sunlight (before 10 AM) daily. Include eggs, fish, or fortified milk. Consider supplementation if levels are very low.",
    "vitamin_b12": "B12 deficiency is common in vegetarians and vegans. Ensure daily intake through dairy/eggs or B12-fortified foods. Supplement if needed (methylcobalamin preferred).",
    "zinc":        "Soak nuts and legumes before cooking to reduce phytates and improve zinc bioavailability. Include protein-rich meals — protein enhances zinc absorption.",
    "magnesium":   "Magnesium supports 300+ enzyme reactions. Prioritise nuts, seeds, and leafy greens. Magnesium glycinate supplement is well-tolerated if dietary intake is insufficient.",
    "vitamin_c":   "Consume Vitamin C-rich foods raw or lightly cooked. Amla (Indian gooseberry) is among the highest natural sources at 600mg/100g, much higher than citrus.",
}

# ── Weekly meal plan templates (Indian-centric) ───────────────────────────────

WEEKLY_MEAL_TEMPLATES_VEG = [
    {"day": "Monday",    "breakfast": ["Poha with peanuts and lemon",     "Amla juice"],             "lunch":  ["Dal + Brown rice + Palak sabzi",     "Curd"],  "dinner": ["Rajma chawal",                        "Salad"],         "snacks": ["Dates + Cashews",   "Guava"]},
    {"day": "Tuesday",   "breakfast": ["Moong dal chilla",               "Orange juice"],            "lunch":  ["Paneer bhurji + Roti + Raita",       "Salad"], "dinner": ["Vegetable dal + Rice",                 "Curd"],          "snacks": ["Almonds",           "Banana"]},
    {"day": "Wednesday", "breakfast": ["Methi paratha + Curd",           "Amla juice"],             "lunch":  ["Chickpea curry + Roti",              "Onion salad"], "dinner": ["Palak paneer + Rice",           "Raita"],         "snacks": ["Pumpkin seeds",     "Orange"]},
    {"day": "Thursday",  "breakfast": ["Upma with vegetables",           "Milk"],                   "lunch":  ["Mixed dal + Brown rice + Spinach",   "Curd"],  "dinner": ["Tofu / Paneer curry + Roti",           "Salad"],         "snacks": ["Dates + Sesame ladoo", "Guava"]},
    {"day": "Friday",    "breakfast": ["Idli + Sambar",                  "Coconut chutney"],        "lunch":  ["Rajma + Roti + Raita",              "Pickle"], "dinner": ["Dal tadka + Jeera rice",               "Curd"],          "snacks": ["Cashews + Almonds", "Lemon water"]},
    {"day": "Saturday",  "breakfast": ["Pesarattu (moong dosa) + Chutney", "Milk"],                 "lunch":  ["Chole + Roti + Salad",              "Curd"],  "dinner": ["Dal makhni + Brown rice",              "Papad"],         "snacks": ["Peanuts",           "Amla"]},
    {"day": "Sunday",    "breakfast": ["Rava dosa + Sambar",             "Amla juice"],             "lunch":  ["Palak dal + Rice + Spinach raita",   "Salad"], "dinner": ["Paneer tikka masala + Roti",            "Raita"],         "snacks": ["Sesame chikki",     "Orange juice"]},
]

WEEKLY_MEAL_TEMPLATES_NONVEG = [
    {"day": "Monday",    "breakfast": ["Egg omelette with vegetables",   "Milk"],            "lunch":  ["Chicken curry + Rice + Dal",         "Raita"],  "dinner": ["Fish curry + Brown rice",              "Salad"],         "snacks": ["Boiled eggs",        "Amla juice"]},
    {"day": "Tuesday",   "breakfast": ["Egg bhurji + Roti",             "Orange juice"],    "lunch":  ["Mutton keema + Roti + Salad",         "Curd"],   "dinner": ["Dal + Rice + Palak sabzi",             "Raita"],         "snacks": ["Cashews",            "Banana"]},
    {"day": "Wednesday", "breakfast": ["Poha + Egg",                    "Milk"],            "lunch":  ["Chicken biryani + Raita",             "Salad"],  "dinner": ["Fish fry + Dal + Rice",                "Curd"],          "snacks": ["Pumpkin seeds",      "Guava"]},
    {"day": "Thursday",  "breakfast": ["Idli + Sambar + Boiled egg",    "Coconut chutney"],"lunch":  ["Prawn curry + Rice + Vegetables",     "Pickle"], "dinner": ["Chicken curry + Roti",                 "Salad"],         "snacks": ["Almonds",            "Lemon water"]},
    {"day": "Friday",    "breakfast": ["Ragi dosa + Egg bhurji",        "Milk"],            "lunch":  ["Tuna rice bowl + Vegetables",          "Curd"],   "dinner": ["Dal makhni + Chicken tikka + Roti",    "Salad"],         "snacks": ["Boiled eggs",        "Dates"]},
    {"day": "Saturday",  "breakfast": ["Egg paratha",                   "Orange juice"],    "lunch":  ["Fish curry + Brown rice + Dal",        "Raita"],  "dinner": ["Mutton curry + Roti + Salad",           "Curd"],          "snacks": ["Peanuts",            "Amla"]},
    {"day": "Sunday",    "breakfast": ["Egg omelette + Toast",          "Milk"],            "lunch":  ["Chicken biriyani + Raita + Salad",     "Pickle"], "dinner": ["Prawns masala + Rice + Dal",            "Curd"],          "snacks": ["Mixed nuts",         "Orange"]},
]


class RecommendationService:

    @staticmethod
    def _get_rda(user: User) -> Dict[str, Dict]:
        """ICMR/WHO RDA targets adjusted for age and gender (in standard units)."""
        is_female = (user.gender is not None and str(user.gender).strip().lower() in ("female", "f", "1"))
        age = user.age or 30

        iron_rda   = 21.0 if (is_female and age < 50) else 17.0
        calcium_rda = 1200.0 if ((is_female and age > 50) or (not is_female and age > 70)) else 1000.0
        vit_d_rda  = 20.0 if age > 70 else 15.0
        vit_b12_rda = 2.4
        zinc_rda   = 8.0 if is_female else 11.0
        mag_rda    = 310.0 if is_female else 400.0
        vit_c_rda  = 65.0 if (is_female and age > 50) else (90.0 if not is_female else 75.0)

        return {
            "iron":       {"value": iron_rda,    "unit": "mg"},
            "calcium":    {"value": calcium_rda, "unit": "mg"},
            "vitamin_d":  {"value": vit_d_rda,   "unit": "mcg"},
            "vitamin_b12":{"value": vit_b12_rda, "unit": "mcg"},
            "zinc":       {"value": zinc_rda,    "unit": "mg"},
            "magnesium":  {"value": mag_rda,     "unit": "mg"},
            "vitamin_c":  {"value": vit_c_rda,   "unit": "mg"},
        }

    @staticmethod
    def get_nutrient_targets(user: User, current_totals: Optional[Dict[str, float]] = None) -> List[NutrientTarget]:
        """Return RDA targets with current intake comparisons."""
        rda = RecommendationService._get_rda(user)
        current = current_totals or {}

        label_map = {
            "iron": "Iron", "calcium": "Calcium", "vitamin_d": "Vitamin D",
            "vitamin_b12": "Vitamin B12", "zinc": "Zinc",
            "magnesium": "Magnesium", "vitamin_c": "Vitamin C",
        }
        intake_key_map = {
            "iron": "iron_mg", "calcium": "calcium_mg",
            "vitamin_d": "vitamin_d_mcg", "vitamin_b12": "vitamin_b12_mcg",
            "zinc": "zinc_mg", "magnesium": "magnesium_mg", "vitamin_c": "vitamin_c_mg",
        }

        targets = []
        for nut, config in rda.items():
            cur = current.get(intake_key_map.get(nut, nut), 0.0)
            pct = min(round((cur / config["value"]) * 100, 1), 200.0) if config["value"] > 0 else 0.0
            targets.append(NutrientTarget(
                nutrient=label_map[nut],
                target_value=config["value"],
                current_value=round(cur, 2),
                unit=config["unit"],
                percentage_achieved=pct,
            ))
        return targets

    @staticmethod
    def query_db_foods(db: Session, nutrient: str, limit: int = 3, is_vegetarian: Optional[bool] = None) -> List[RecommendationFoodItem]:
        """Query PG food catalog for highest-value foods for the target nutrient."""
        col_map = {
            "iron":       (FoodCatalog.iron_mg,         "mg"),
            "calcium":    (FoodCatalog.calcium_mg,       "mg"),
            "vitamin_d":  (FoodCatalog.vitamin_d_mcg,    "mcg"),
            "vitamin_b12":(FoodCatalog.vitamin_b12_mcg,  "mcg"),
            "zinc":       (FoodCatalog.zinc_mg,          "mg"),
            "magnesium":  (FoodCatalog.magnesium_mg,     "mg"),
            "vitamin_c":  (FoodCatalog.vitamin_c_mg,     "mg"),
        }
        if nutrient not in col_map:
            return []

        db_col, unit = col_map[nutrient]
        try:
            results = (
                db.query(FoodCatalog)
                .filter(db_col.isnot(None), db_col > 0)
                .filter(FoodCatalog.food_name.not_like("%powder%"))
                .filter(FoodCatalog.food_name.not_like("%supplement%"))
                .filter(FoodCatalog.food_name.not_like("%infant%"))
                .order_by(desc(db_col))
                .limit(limit)
                .all()
            )
            return [
                RecommendationFoodItem(
                    food_name=item.food_name,
                    nutrient_amount=round(float(getattr(item, db_col.key)), 2),
                    unit=unit,
                    is_vegetarian=True,
                    is_indian=(item.cuisine_type == "Indian") if item.cuisine_type else False,
                )
                for item in results
            ]
        except Exception:
            return []

    @classmethod
    def generate_recommendations(
        cls,
        db: Session,
        user: User,
        risks: Dict[str, float],
        current_totals: Optional[Dict[str, float]] = None,
    ) -> RecommendationsOut:
        """
        Build complete recommendations based on deficiency risks.
        Prioritises Indian foods and respects vegetarian preferences.
        """
        is_vegetarian = (
            user.diet_preference is not None and
            user.diet_preference.strip().lower() in ("vegetarian", "vegan")
        )

        # Rank by risk score
        sorted_risks = sorted(risks.items(), key=lambda x: x[1], reverse=True)
        deficient_keys = [k for k, r in sorted_risks if r >= 0.45]
        if not deficient_keys and sorted_risks:
            deficient_keys = [sorted_risks[0][0]]

        foods_to_eat: List[RecommendationFoodItem] = []
        foods_to_avoid: List[str] = []
        advice_parts: List[str] = []

        for nut in deficient_keys:
            # DB foods first
            db_foods = cls.query_db_foods(db, nut, limit=2)
            foods_to_eat.extend(db_foods)

            # Add static list (filter vegetarian if needed)
            for item in STATIC_FOODS.get(nut, []):
                if is_vegetarian and not item["is_vegetarian"]:
                    continue
                if not any(f.food_name.lower() == item["food_name"].lower() for f in foods_to_eat):
                    foods_to_eat.append(
                        RecommendationFoodItem(
                            food_name=item["food_name"],
                            nutrient_amount=item.get("nutrient_amount", item.get("amount", 0.0)),
                            unit=item["unit"],
                            is_vegetarian=item.get("is_vegetarian", True),
                            is_indian=item.get("is_indian", False),
                            meal_suggestion=item.get("meal_suggestion"),
                        )
                    )

            if nut in FOODS_TO_AVOID:
                foods_to_avoid.append(FOODS_TO_AVOID[nut])
            if nut in HEALTH_ADVICE:
                advice_parts.append(HEALTH_ADVICE[nut])

        # Sort Indian foods first, cap at 8
        foods_to_eat.sort(key=lambda x: (0 if x.is_indian else 1))
        foods_to_eat = foods_to_eat[:8]

        short_advice = " · ".join(advice_parts) if advice_parts else (
            "Maintain a balanced diet rich in whole grains, proteins, and fresh leafy vegetables. "
            "Include seasonal fruits and fermented foods (curd, idli, dosa) for gut health."
        )

        targets = cls.get_nutrient_targets(user, current_totals)

        # Generate weekly meal plan
        weekly_plan = cls.generate_weekly_meal_plan(
            deficiency_keys=deficient_keys,
            diet_preference=user.diet_preference or "Non-Vegetarian"
        )

        weekly_plan_out = [
            DayMealPlan(
                day=d["day"],
                breakfast=d["breakfast"],
                lunch=d["lunch"],
                dinner=d["dinner"],
                snacks=d["snacks"]
            )
            for d in weekly_plan.get("days", [])
        ]

        return RecommendationsOut(
            foods_to_eat=foods_to_eat,
            foods_to_avoid=foods_to_avoid,
            daily_nutrient_targets=targets,
            short_health_advice=short_advice,
            weekly_meal_plan=weekly_plan_out,
        )

    @staticmethod
    def generate_weekly_meal_plan(
        deficiency_keys: List[str],
        diet_preference: str = "Non-Vegetarian"
    ) -> Dict[str, Any]:
        """
        Generate a structured 7-day meal plan prioritising foods that address
        the detected deficiencies.
        """
        is_veg = diet_preference.strip().lower() in ("vegetarian", "vegan")
        base_template = WEEKLY_MEAL_TEMPLATES_VEG if is_veg else WEEKLY_MEAL_TEMPLATES_NONVEG

        # Build enrichment foods per deficiency (Indian-first, vegetarian-appropriate)
        enrichment: Dict[str, List[str]] = {}
        for nut in deficiency_keys:
            foods = [
                item["food_name"]
                for item in STATIC_FOODS.get(nut, [])
                if not (is_veg and not item["is_vegetarian"])
            ][:3]
            enrichment[nut] = foods

        # Add deficiency-specific foods to snack slots
        days_out = []
        for i, day_tmpl in enumerate(base_template):
            snacks = list(day_tmpl["snacks"])
            for nut in deficiency_keys[:2]:  # top 2 deficiencies
                additions = enrichment.get(nut, [])
                for food in additions:
                    # Avoid duplicating already present items
                    if food not in snacks and food not in day_tmpl["breakfast"] \
                            and food not in day_tmpl["lunch"] and food not in day_tmpl["dinner"]:
                        snacks.append(food)
                        break

            days_out.append({
                "day": day_tmpl["day"],
                "breakfast": day_tmpl["breakfast"],
                "lunch": day_tmpl["lunch"],
                "dinner": day_tmpl["dinner"],
                "snacks": snacks[:4],           # cap at 4 snack items
            })

        return {
            "diet_preference": diet_preference,
            "deficiency_focus": deficiency_keys,
            "days": days_out,
        }
