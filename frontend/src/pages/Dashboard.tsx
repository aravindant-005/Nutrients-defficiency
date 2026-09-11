import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  authAPI,
  predictAPI,
  foodLogAPI
} from '../services/api';
import type {
  UserProfile,
  PredictionHistoryItem,
  DailySummary,
  FoodLogItem
} from '../services/api';
import {
  Activity,
  Plus,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Zap,
  User,
  Flame,
  Beef,
  Droplets,
  UtensilsCrossed,
  Scale,
  RefreshCw,
  Heart,
  Dumbbell
} from 'lucide-react';

const NUTRIENT_KEYS: { key: keyof PredictionHistoryItem; label: string }[] = [
  { key: 'iron_risk',        label: 'Iron'        },
  { key: 'calcium_risk',     label: 'Calcium'     },
  { key: 'vitamin_d_risk',   label: 'Vitamin D'   },
  { key: 'vitamin_b12_risk', label: 'Vitamin B12' },
  { key: 'zinc_risk',        label: 'Zinc'        },
];

function riskColor(score: number): string {
  if (score >= 0.70) return 'text-rose-400';
  if (score >= 0.45) return 'text-amber-400';
  return 'text-emerald-400';
}

function riskBadge(score: number): string {
  if (score >= 0.70) return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  if (score >= 0.45) return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
}

function riskLabel(score: number): string {
  if (score >= 0.70) return 'High Risk';
  if (score >= 0.45) return 'Moderate';
  return 'Low Risk';
}

function bmiCategory(bmi: number): { label: string; color: string; desc: string } {
  if (bmi < 18.5) return { label: 'Underweight', color: 'text-sky-400', desc: 'Focus on calorie-dense whole foods.' };
  if (bmi < 25.0) return { label: 'Normal weight', color: 'text-emerald-400', desc: 'Excellent. Keep up your balanced diet.' };
  if (bmi < 30.0) return { label: 'Overweight', color: 'text-amber-400', desc: 'Incorporate portion control & daily cardio.' };
  return { label: 'Obese', color: 'text-rose-400', desc: 'Focus on lifestyle modifications & consult a dietitian.' };
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile]     = useState<UserProfile | null>(null);
  const [history, setHistory]     = useState<PredictionHistoryItem[]>([]);
  const [summary, setSummary]     = useState<DailySummary | null>(null);
  const [foodLogs, setFoodLogs]   = useState<FoodLogItem[]>([]);
  
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    setRefreshing(true);
    try {
      const [pRes, hRes, sRes, fRes] = await Promise.all([
        authAPI.me(),
        predictAPI.history(),
        foodLogAPI.summary(),
        foodLogAPI.list(),
      ]);
      setProfile(pRes.data);
      setHistory(hRes.data);
      setSummary(sRes.data);
      setFoodLogs(fRes.data);
    } catch (e) {
      console.error('Error fetching dashboard statistics:', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-500">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent mb-3" />
        <p className="text-sm font-medium">Gathering health reports...</p>
      </div>
    );
  }

  const latest = history[0];
  const highRiskCount = latest
    ? NUTRIENT_KEYS.filter(({ key }) => (latest[key] as number) >= 0.70).length
    : 0;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* ── Top Header Actions ── */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-200">Clinical Dashboard</h2>
          <p className="text-xs text-slate-500">AI-powered wellness indicators</p>
        </div>
        <button
          onClick={loadData}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* ── Welcome & Profile Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* Welcome Card */}
        <div className="lg:col-span-5 relative overflow-hidden rounded-xl bg-gradient-to-br from-emerald-500/20 via-teal-500/10 to-slate-950 border border-emerald-500/20 p-6 flex flex-col justify-between">
          <div className="relative z-10 space-y-3">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Sparkles className="h-3 w-3" /> Health Status Active
            </span>
            <h2 className="text-2xl font-bold text-slate-100">{getGreeting()}, {profile?.name}!</h2>
            <p className="text-xs text-slate-400 leading-relaxed max-w-sm">
              Your metabolic parameters and nutrient profiles are up to date. Explore targeted recommendations below.
            </p>
          </div>
          <div className="flex gap-2 mt-6">
            <button
              onClick={() => navigate('/predict')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-emerald-500/10"
            >
              <Activity className="h-3.5 w-3.5" /> Run Predictor
            </button>
            <button
              onClick={() => navigate('/food-log')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 font-semibold text-xs transition-all"
            >
              <Plus className="h-3.5 w-3.5" /> Log a Meal
            </button>
          </div>
        </div>

        {/* User Profile Summary */}
        <div className="lg:col-span-4 glass-panel p-6 rounded-xl space-y-4">
          <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
            <User className="h-4 w-4 text-emerald-400" /> Physiological Profile
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Age</span>
              <span className="text-sm font-semibold text-slate-300">{profile?.age ?? '—'} yrs</span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Gender</span>
              <span className="text-sm font-semibold text-slate-300">{profile?.gender ?? '—'}</span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Height</span>
              <span className="text-sm font-semibold text-slate-300">{profile?.height ?? '—'} cm</span>
            </div>
            <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Weight</span>
              <span className="text-sm font-semibold text-slate-300">{profile?.weight ?? '—'} kg</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 border-t border-slate-900/80 pt-3">
            <Dumbbell className="h-3.5 w-3.5 text-indigo-400" />
            Activity Level: <span className="text-slate-300 font-semibold">{profile?.activity_level ?? 'Moderate'}</span>
          </div>
        </div>

        {/* BMI Card */}
        <div className="lg:col-span-3 glass-panel p-6 rounded-xl flex flex-col justify-between">
          <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
            <Scale className="h-4 w-4 text-indigo-400" /> Body Mass Index
          </h3>
          <div className="my-auto py-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-200">{profile?.bmi?.toFixed(1) ?? '—'}</span>
            <span className="text-xs text-slate-500">kg/m²</span>
          </div>
          <div className="space-y-1">
            <p className={`text-xs font-bold ${profile?.bmi ? bmiCategory(profile.bmi).color : 'text-slate-500'}`}>
              {profile?.bmi ? bmiCategory(profile.bmi).label : 'Not calculated'}
            </p>
            <p className="text-[10px] text-slate-500 leading-normal">
              {profile?.bmi ? bmiCategory(profile.bmi).desc : 'Update height/weight to calculate your index.'}
            </p>
          </div>
        </div>

      </div>

      {/* ── Today's Nutrition Grid (9 parameters) ── */}
      <div className="space-y-3">
        <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
          <Heart className="h-4 w-4 text-rose-500" /> Today's Cumulative Nutrition Summary
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-5 lg:grid-cols-9 gap-3">
          {[
            { label: 'Calories', value: summary?.calories ?? 0.0, unit: 'kcal', icon: Flame,    color: 'amber'   },
            { label: 'Protein',  value: summary?.protein ?? 0.0,  unit: 'g',    icon: Beef,     color: 'rose'    },
            { label: 'Carbs',    value: summary?.carbohydrates ?? 0.0, unit: 'g', icon: Zap,    color: 'sky'     },
            { label: 'Fat',      value: summary?.fat ?? 0.0,       unit: 'g',    icon: Droplets, color: 'violet'  },
            { label: 'Iron',     value: summary?.iron ?? 0.0,      unit: 'mg',   icon: Activity, color: 'emerald' },
            { label: 'Calcium',  value: summary?.calcium ?? 0.0,   unit: 'mg',   icon: Activity, color: 'sky'     },
            { label: 'Vitamin D', value: summary?.vitamin_d ?? 0.0, unit: 'mcg', icon: Activity, color: 'amber'   },
            { label: 'Vit B12',  value: summary?.vitamin_b12 ?? 0.0, unit: 'mcg', icon: Activity, color: 'violet'  },
            { label: 'Zinc',     value: summary?.zinc ?? 0.0,      unit: 'mg',   icon: Activity, color: 'rose'    },
          ].map(({ label, value, unit, icon: Icon, color }) => (
            <div key={label} className="glass-panel p-4 rounded-xl border border-slate-900 text-center flex flex-col justify-between">
              <span className={`text-${color}-400 mx-auto mb-1`}><Icon className="h-4 w-4" /></span>
              <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">{label}</p>
              <p className="text-base font-bold text-slate-200 mt-1">{value.toFixed(1)}</p>
              <span className="text-[9px] text-slate-600 block mt-0.5">{unit}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Logs and History Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* Recent Food Logs */}
        <div className="lg:col-span-6 glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
          <div className="px-5 py-4 border-b border-slate-900 flex justify-between items-center">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
              <UtensilsCrossed className="h-4 w-4 text-emerald-400" /> Recent Meals Today
            </h3>
            <Link to="/food-log" className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold">
              Manage logs
            </Link>
          </div>
          <div className="divide-y divide-slate-900/60 flex-1 overflow-y-auto max-h-[280px]">
            {foodLogs.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <p className="text-xs">No food logs submitted today.</p>
                <button
                  onClick={() => navigate('/food-log')}
                  className="text-xs text-emerald-400 font-bold hover:underline mt-2"
                >
                  + Add first food log
                </button>
              </div>
            ) : (
              foodLogs.slice(0, 4).map((log) => (
                <div key={log.id} className="p-4 flex justify-between items-center text-xs">
                  <div>
                    <p className="font-bold text-slate-200">{log.food_name}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      {log.quantity}{log.serving_size} · {log.meal_type}
                    </p>
                  </div>
                  <span className="font-mono text-slate-400">{log.calories?.toFixed(0)} kcal</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Prediction History */}
        <div className="lg:col-span-6 glass-panel rounded-xl overflow-hidden flex flex-col justify-between">
          <div className="px-5 py-4 border-b border-slate-900 flex justify-between items-center">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-indigo-400" /> Deficiency Risk History
              {highRiskCount > 0 && (
                <span className="text-[10px] bg-rose-500/20 text-rose-400 border border-rose-500/30 px-1.5 py-0.5 rounded ml-2 flex items-center gap-1 shrink-0">
                  <ShieldAlert className="h-3 w-3" /> {highRiskCount} alert{highRiskCount !== 1 ? 's' : ''}
                </span>
              )}
            </h3>
            <Link to="/predict" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold">
              New assessment
            </Link>
          </div>
          
          <div className="flex-1 p-5 flex flex-col justify-between gap-4">
            {!latest ? (
              <div className="text-center py-8 text-slate-500">
                <p className="text-xs">No deficiency predictions found.</p>
                <Link to="/predict" className="text-xs text-emerald-400 hover:underline mt-2 block">
                  Calculate deficiency risk profile →
                </Link>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-400">Nutrient Risk Levels</span>
                  <span className="text-[10px] text-slate-500">
                    Last Run: {new Date(latest.prediction_date).toLocaleDateString()}
                  </span>
                </div>

                <div className="grid grid-cols-5 gap-2">
                  {NUTRIENT_KEYS.map(({ key, label }) => {
                    const score = latest[key] as number;
                    return (
                      <div key={key} className={`p-2.5 rounded-lg border text-center flex flex-col justify-between ${riskBadge(score)}`}>
                        <span className="text-[9px] font-semibold text-slate-500 block truncate">{label}</span>
                        <span className={`text-base font-bold my-1 ${riskColor(score)}`}>{Math.round(score * 100)}%</span>
                        <span className={`text-[8px] font-semibold ${riskColor(score)} truncate`}>{riskLabel(score)}</span>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
