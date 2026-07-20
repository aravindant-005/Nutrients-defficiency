import os
from datetime import datetime
from sqlalchemy import select
from app.core.database import engine, SessionLocal
from app.models.deficiency import FoodCatalog, FoodLog, User


def print_counts(session):
    fc_count = session.query(FoodCatalog).count()
    fl_count = session.query(FoodLog).count()
    users = session.query(User).count()
    print(f"food_catalog rows: {fc_count}")
    print(f"food_logs rows:    {fl_count}")
    print(f"users rows:        {users}")


def sample_food_catalog(session, q=None, limit=10):
    print('\n--- food_catalog sample')
    if q:
        print(f"Searching for '{q}' (case-insensitive)...")
        items = session.query(FoodCatalog).filter(FoodCatalog.food_name.ilike(f"%{q}%"))
    else:
        items = session.query(FoodCatalog)
    items = items.limit(limit).all()
    for i in items:
        print('-', i.food_name[:120])


def recent_food_logs(session, limit=10):
    print('\n--- recent food_logs')
    rows = session.query(FoodLog).order_by(FoodLog.logged_at.desc()).limit(limit).all()
    for r in rows:
        print(f"id={r.id} user_id={r.user_id} name={r.food_name[:80]} logged_at={r.logged_at} qty={r.quantity} meal_type={r.meal_type}")


def run_prediction_demo():
    # Import late to avoid heavy imports when not needed
    from app.ml.model import run_prediction

    print('\n--- prediction demo: varying gender and nutrient totals')
    common = dict(age=30, gender=0, weight_kg=70, height_cm=170, bmi=24.2, activity_level=None)

    # baseline (no food logged)
    p1 = run_prediction(**common, nutrient_totals={
        'calories_kcal': 0, 'protein_g':0, 'carbs_g':0, 'fat_g':0, 'fiber_g':0,
        'iron_mg':0,'calcium_mg':0,'magnesium_mg':0,'zinc_mg':0,'vitamin_c_mg':0,
        'vitamin_d_mcg':0,'vitamin_b12_mcg':0,'vitamin_b6_mg':0,'vitamin_a_mcg':0,
    })
    print('baseline predictions keys:', sorted(p1.keys()))
    for k,v in p1.items():
        print(k, '->', v)

    # high-iron meal
    p2 = run_prediction(**common, nutrient_totals={
        'calories_kcal': 600, 'protein_g':30, 'carbs_g':60, 'fat_g':20, 'fiber_g':10,
        'iron_mg':15,'calcium_mg':200,'magnesium_mg':80,'zinc_mg':5,'vitamin_c_mg':60,
        'vitamin_d_mcg':2,'vitamin_b12_mcg':3,'vitamin_b6_mg':0.5,'vitamin_a_mcg':50,
    })
    print('\nwith high-iron meal:')
    for k,v in p2.items():
        print(k, '->', v)


if __name__ == '__main__':
    print('Using DB URL from settings...')
    sess = SessionLocal()
    try:
        print_counts(sess)
        sample_food_catalog(sess, q='indian', limit=5)
        sample_food_catalog(sess, q='rice', limit=5)
        recent_food_logs(sess, limit=10)
        run_prediction_demo()
    finally:
        sess.close()
