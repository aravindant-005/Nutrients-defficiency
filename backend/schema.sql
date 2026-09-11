-- PostgreSQL Schema DDL Script for pgAdmin
-- Database: micronutrient_db

CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) DEFAULT 'Dhakshanesh R',
    age FLOAT DEFAULT 28.0,
    gender FLOAT DEFAULT 1.0,
    race FLOAT DEFAULT 3.0,
    weight_kg FLOAT DEFAULT 70.0,
    height_cm FLOAT DEFAULT 175.0,
    bmi FLOAT DEFAULT 22.86,
    activity_level VARCHAR(50) DEFAULT 'Moderate',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS food_log_items (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES user_profiles(id) ON DELETE CASCADE,
    food_code VARCHAR(100),
    food_name VARCHAR(255) NOT NULL,
    serving_size_g FLOAT DEFAULT 100.0,
    calories_kcal FLOAT DEFAULT 0.0,
    protein_g FLOAT DEFAULT 0.0,
    carbs_g FLOAT DEFAULT 0.0,
    fat_g FLOAT DEFAULT 0.0,
    fiber_g FLOAT DEFAULT 0.0,
    iron_mg FLOAT DEFAULT 0.0,
    calcium_mg FLOAT DEFAULT 0.0,
    vitamin_d_mcg FLOAT DEFAULT 0.0,
    vitamin_b12_mcg FLOAT DEFAULT 0.0,
    zinc_mg FLOAT DEFAULT 0.0,
    magnesium_mg FLOAT DEFAULT 0.0,
    vitamin_c_mg FLOAT DEFAULT 0.0,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prediction_results (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES user_profiles(id) ON DELETE CASCADE,
    nutrient VARCHAR(100) NOT NULL,
    risk_probability FLOAT NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    top_factor VARCHAR(255),
    explanation TEXT,
    recommended_foods TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
