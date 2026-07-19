from fastapi import APIRouter
from app.api.v1.endpoints import auth, predict, history, food_log, food_catalog, dashboard, recommendations, meal_plan

api_router = APIRouter()

# Core authentication & user management
api_router.include_router(auth.router,            prefix="/auth",            tags=["auth"])

# Food logging
api_router.include_router(food_log.router,        prefix="/food-log",        tags=["food-log"])
api_router.include_router(food_catalog.router,    prefix="/food-catalog",    tags=["food-catalog"])

# Prediction & ML
api_router.include_router(predict.router,         prefix="/predict",         tags=["predict"])

# Recommendations & meal planning
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(meal_plan.router,       prefix="/meal-plan",       tags=["meal-plan"])

# Dashboard & history
api_router.include_router(dashboard.router,       prefix="/dashboard",       tags=["dashboard"])
api_router.include_router(history.router,         prefix="/history",         tags=["history"])
