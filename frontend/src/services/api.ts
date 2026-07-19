import axios from 'axios';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Automatically inject JWT tokens into all request headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ShapFeature {
  feature: string;
  value: number;
  contribution: number;
}

export interface NutrientRisk {
  risk_score: number;
  risk_label: 'Low' | 'Moderate' | 'High';
  explanation: ShapFeature[] | null;
}

export interface PredictInput {
  age: number;
  gender: string;          // Male / Female / Other
  weight_kg: number;
  height_cm: number;
  bmi: number;
  include_shap: boolean;
}

export interface RecommendationFoodItem {
  food_name: string;
  nutrient_amount: number;
  unit: string;
}

export interface NutrientTarget {
  nutrient: string;
  target_value: number;
  unit: string;
}

export interface RecommendationsOut {
  foods_to_eat: RecommendationFoodItem[];
  foods_to_avoid: string[];
  daily_nutrient_targets: NutrientTarget[];
  short_health_advice: string;
}

export interface PredictResponse {
  user_id: number;
  prediction_date: string;
  results: Record<string, NutrientRisk>;
  iron_risk: number;
  calcium_risk: number;
  vitamin_d_risk: number;
  vitamin_b12_risk: number;
  zinc_risk: number;
  recommendations?: RecommendationsOut | null;
}

export interface PredictionHistoryItem {
  id: number;
  user_id: number;
  iron_risk: number;
  calcium_risk: number;
  vitamin_d_risk: number;
  vitamin_b12_risk: number;
  zinc_risk: number;
  prediction_date: string;
}

export interface FoodLogCreate {
  food_name: string;
  quantity: number;
  serving_size: string;
  meal_type: 'Breakfast' | 'Lunch' | 'Dinner' | 'Snack';
  calories?: number;
  protein?: number;
  carbohydrates?: number;
  fat?: number;
  iron?: number;
  calcium?: number;
  vitamin_d?: number;
  vitamin_b12?: number;
  zinc?: number;
}

export interface FoodLogItem extends FoodLogCreate {
  id: number;
  user_id: number;
  logged_at: string;
}

export interface DailySummary {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  iron: number;
  calcium: number;
  vitamin_d: number;
  vitamin_b12: number;
  zinc: number;
}

// ── API Methods ────────────────────────────────────────────────────────────────

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  age: number | null;
  gender: string | null;
  height: number | null;
  weight: number | null;
  bmi: number | null;
  activity_level: string | null;
  created_at: string;
}

export const authAPI = {
  me: () =>
    api.get<UserProfile>('auth/me'),
};

export const predictAPI = {
  run: (input: PredictInput) =>
    api.post<PredictResponse>('predict/', input),
  history: () =>
    api.get<PredictionHistoryItem[]>('predict/history'),
};

export const foodLogAPI = {
  create: (data: FoodLogCreate) =>
    api.post<FoodLogItem>('food-log/', data),
  list: (dateStr?: string) =>
    api.get<FoodLogItem[]>('food-log/', { params: dateStr ? { date_str: dateStr } : {} }),
  delete: (id: number) =>
    api.delete(`food-log/${id}`),
  summary: (dateStr?: string) =>
    api.get<DailySummary>('food-log/summary', { params: dateStr ? { date_str: dateStr } : {} }),
};

export interface FoodCatalogItem {
  id: number;
  fdc_id: number | null;
  food_name: string;
  source: string | null;
  calories_kcal: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  iron_mg: number | null;
  calcium_mg: number | null;
  vitamin_d_mcg: number | null;
  vitamin_b12_mcg: number | null;
  zinc_mg: number | null;
}

export const foodCatalogAPI = {
  search: (q: string) =>
    api.get<FoodCatalogItem[]>('food-catalog/search', { params: { q } }),
};

export function parseApiError(err: any): string {
  if (!err) return 'An unexpected error occurred.';

  if (err.code === 'ERR_NETWORK' || err.message === 'Network Error') {
    return 'Network error: cannot reach the API at http://localhost:8000. Ensure the backend is running and CORS is enabled.';
  }

  if (err.request && !err.response) {
    return 'No response from the server. Please verify the backend is running and the API URL is correct.';
  }

  const detail = err.response?.data?.detail;
  if (!detail) {
    return err.response?.status
      ? `Request failed with status ${err.response.status}: ${err.message}`
      : err.message || 'An unexpected error occurred.';
  }

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item: any) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && item.msg) {
          const field = Array.isArray(item.loc)
            ? item.loc.filter((l: any) => l !== 'body').join('.')
            : '';
          return field ? `${field}: ${item.msg}` : item.msg;
        }
        return JSON.stringify(item);
      })
      .join(', ');
  }

  if (typeof detail === 'object') {
    return detail.message || JSON.stringify(detail);
  }

  return String(detail);
}

export default api;
