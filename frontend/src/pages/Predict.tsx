import React, { useState, useEffect } from 'react';
import { predictAPI, parseApiError } from '../services/api';
import type { PredictResponse, NutrientRisk, PredictionHistoryItem, RecommendationFoodItem, NutrientTarget } from '../services/api';
import {
  ShieldCheck,
  BrainCircuit,
  Activity,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Info,
  Utensils,
  ChevronRight,
  TrendingDown,
  Apple,
  XCircle,
  Target
} from 'lucide-react';

const NUTRIENTS: { key: string; label: string; color: string }[] = [
  { key: 'iron',        label: 'Iron',        color: 'emerald' },
  { key: 'calcium',     label: 'Calcium',     color: 'sky'     },
  { key: 'vitamin_d',   label: 'Vitamin D',   color: 'amber'   },
  { key: 'vitamin_b12', label: 'Vitamin B12', color: 'violet'  },
  { key: 'zinc',        label: 'Zinc',        color: 'rose'    },
];

const RISK_CONFIG = {
  High:     { icon: AlertTriangle, textClass: 'text-rose-400',    barClass: 'bg-rose-500',    bgClass: 'bg-rose-500/10 border-rose-500/30'    },
  Moderate: { icon: Info,          textClass: 'text-amber-400',   barClass: 'bg-amber-500',   bgClass: 'bg-amber-500/10 border-amber-500/30'   },
  Low:      { icon: CheckCircle,   textClass: 'text-emerald-400', barClass: 'bg-emerald-500', bgClass: 'bg-emerald-500/10 border-emerald-500/30'},
  Unknown:  { icon: Activity,      textClass: 'text-slate-400',   barClass: 'bg-slate-500',   bgClass: 'bg-slate-800 border-slate-700'          },
};

function computeBMI(weight: number, height: number): number {
  if (!weight || !height) return 0;
  return parseFloat((weight / ((height / 100) ** 2)).toFixed(1));
}

const Predict: React.FC = () => {
  const [age, setAge]           = useState<number>(30);
  const [gender, setGender]     = useState<'Male' | 'Female'>('Male');
  const [weight, setWeight]     = useState<number>(70);
  const [height, setHeight]     = useState<number>(170);
  const [includeShap, setIncludeShap] = useState(true);
  const [activeShap, setActiveShap]   = useState<string>('iron');

  const [loading, setLoading]   = useState(false);
  const [results, setResults]   = useState<PredictResponse | null>(null);
  const [error, setError]       = useState<string | null>(null);
  const [history, setHistory]   = useState<PredictionHistoryItem[]>([]);

  const bmi = computeBMI(weight, height);

  const fetchHistory = async () => {
    try {
      const { data } = await predictAPI.history();
      setHistory(data);
    } catch (e) {
      console.error('Error fetching checkup history:', e);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const { data } = await predictAPI.run({
        age,
        gender,
        weight_kg: weight,
        height_cm: height,
        bmi,
        include_shap: includeShap,
      });
      setResults(data);
      setActiveShap('iron');
      fetchHistory(); // Refresh history panel
    } catch (err: any) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistory = (item: PredictionHistoryItem) => {
    const mockResults: Record<string, NutrientRisk> = {
      iron: {
        risk_score: item.iron_risk,
        risk_label: item.iron_risk >= 0.70 ? 'High' : item.iron_risk >= 0.45 ? 'Moderate' : 'Low',
        explanation: null
      },
      calcium: {
        risk_score: item.calcium_risk,
        risk_label: item.calcium_risk >= 0.70 ? 'High' : item.calcium_risk >= 0.45 ? 'Moderate' : 'Low',
        explanation: null
      },
      vitamin_d: {
        risk_score: item.vitamin_d_risk,
        risk_label: item.vitamin_d_risk >= 0.70 ? 'High' : item.vitamin_d_risk >= 0.45 ? 'Moderate' : 'Low',
        explanation: null
      },
      vitamin_b12: {
        risk_score: item.vitamin_b12_risk,
        risk_label: item.vitamin_b12_risk >= 0.70 ? 'High' : item.vitamin_b12_risk >= 0.45 ? 'Moderate' : 'Low',
        explanation: null
      },
      zinc: {
        risk_score: item.zinc_risk,
        risk_label: item.zinc_risk >= 0.70 ? 'High' : item.zinc_risk >= 0.45 ? 'Moderate' : 'Low',
        explanation: null
      }
    };

    const selectedDeficiencies = Object.entries(mockResults)
      .filter(([_, res]) => res.risk_score >= 0.50)
      .map(([k]) => k);
    
    const finalDeficiencies = selectedDeficiencies.length > 0 
      ? selectedDeficiencies 
      : [Object.entries(mockResults).sort((a,b) => b[1].risk_score - a[1].risk_score)[0][0]];

    const foodsToEat: any[] = [];
    const foodsToAvoid: string[] = [];
    const adviceParts: string[] = [];

    const staticFoods = {
      iron: [
        { food_name: "Cooked Lentils", nutrient_amount: 3.3, unit: "mg" },
        { food_name: "Pumpkin Seeds", nutrient_amount: 8.8, unit: "mg" },
        { food_name: "Spinach", nutrient_amount: 2.7, unit: "mg" }
      ],
      calcium: [
        { food_name: "Plain Yogurt", nutrient_amount: 110.0, unit: "mg" },
        { food_name: "Almonds", nutrient_amount: 260.0, unit: "mg" },
        { food_name: "Tofu", nutrient_amount: 350.0, unit: "mg" }
      ],
      vitamin_d: [
        { food_name: "Wild Salmon", nutrient_amount: 10.9, unit: "mcg" },
        { food_name: "Egg Yolks", nutrient_amount: 5.4, unit: "mcg" },
        { food_name: "Fortified Milk", nutrient_amount: 1.3, unit: "mcg" }
      ],
      vitamin_b12: [
        { food_name: "Clams", nutrient_amount: 98.9, unit: "mcg" },
        { food_name: "Beef Liver", nutrient_amount: 59.3, unit: "mcg" },
        { food_name: "Fortified Yeast", nutrient_amount: 49.0, unit: "mcg" }
      ],
      zinc: [
        { food_name: "Oysters", nutrient_amount: 16.6, unit: "mg" },
        { food_name: "Pumpkin Seeds", nutrient_amount: 7.8, unit: "mg" },
        { food_name: "Beef Steak", nutrient_amount: 6.3, unit: "mg" }
      ]
    };

    const staticAvoid = {
      iron: "Avoid drinking black tea or coffee with meals.",
      calcium: "Avoid excessive sodium intake and phosphoric acid.",
      vitamin_d: "Avoid excessive alcohol consumption.",
      vitamin_b12: "Avoid heavy alcohol intake and taking mega-doses of Vitamin C together.",
      zinc: "Avoid consuming raw whole grains or unsoaked legumes."
    };

    const staticAdvice = {
      iron: "Focus on combining iron-rich foods with Vitamin C to boost absorption.",
      calcium: "Ensure adequate daily calcium intake to support bones.",
      vitamin_d: "Boost Vitamin D levels through dietary sources and sunlight.",
      vitamin_b12: "If you follow a plant-based diet, ensure you consume fortified foods.",
      zinc: "Focus on protein-rich foods, which enhance zinc bioavailability."
    };

    finalDeficiencies.forEach(nut => {
      foodsToEat.push(...(staticFoods[nut as keyof typeof staticFoods] || []));
      foodsToAvoid.push(staticAvoid[nut as keyof typeof staticAvoid]);
      adviceParts.push(staticAdvice[nut as keyof typeof staticAdvice]);
    });

    setResults({
      user_id: item.user_id,
      prediction_date: item.prediction_date,
      results: mockResults,
      iron_risk: item.iron_risk,
      calcium_risk: item.calcium_risk,
      vitamin_d_risk: item.vitamin_d_risk,
      vitamin_b12_risk: item.vitamin_b12_risk,
      zinc_risk: item.zinc_risk,
      recommendations: {
        foods_to_eat: foodsToEat.slice(0, 6),
        foods_to_avoid: foodsToAvoid,
        daily_nutrient_targets: [
          { nutrient: "Iron", target_value: 18.0, unit: "mg" },
          { nutrient: "Calcium", target_value: 1000.0, unit: "mg" },
          { nutrient: "Vitamin D", target_value: 15.0, unit: "mcg" },
          { nutrient: "Vitamin B12", target_value: 2.4, unit: "mcg" },
          { nutrient: "Zinc", target_value: 8.0, unit: "mg" }
        ],
        short_health_advice: adviceParts.join(" · ")
      }
    });
    
    setActiveShap(finalDeficiencies[0] || 'iron');
  };

  const renderRiskCard = (key: string, label: string, result: NutrientRisk) => {
    const cfg   = RISK_CONFIG[result.risk_label] ?? RISK_CONFIG.Unknown;
    const Icon  = cfg.icon;
    const pct   = Math.round(result.risk_score * 100);

    return (
      <div
        key={key}
        className={`p-4 rounded-xl border transition-all cursor-pointer ${cfg.bgClass} ${activeShap === key ? 'ring-1 ring-white/20 shadow-md' : ''}`}
        onClick={() => setActiveShap(key)}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Icon className={`h-4 w-4 ${cfg.textClass}`} />
            <span className="text-sm font-semibold text-slate-200">{label}</span>
          </div>
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${cfg.bgClass} ${cfg.textClass} border ${cfg.bgClass.replace('bg-', 'border-').replace('/10', '/40')}`}>
            {result.risk_label}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-slate-900 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-700 ${cfg.barClass}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className={`text-sm font-bold w-10 text-right ${cfg.textClass}`}>{pct}%</span>
        </div>
      </div>
    );
  };

  const activeShapData = results?.results?.[activeShap]?.explanation ?? [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fadeIn">

      {/* ── LEFT PANEL: Questionnaire & Past Checkups (col-span-4) ── */}
      <div className="lg:col-span-4 space-y-6">
        
        {/* Questionnaire Input Card */}
        <div className="glass-panel p-6 rounded-xl">
          <div className="flex items-center gap-3 mb-6">
            <BrainCircuit className="h-5 w-5 text-emerald-400" />
            <h3 className="font-bold text-slate-200">Deficiency Forecaster</h3>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Age</label>
                <span className="text-emerald-400 text-xs font-bold">{age} yrs</span>
              </div>
              <input type="range" min={18} max={90} value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                className="w-full accent-emerald-500" />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Gender</label>
              <div className="grid grid-cols-2 gap-2">
                {[{ label: 'Male' }, { label: 'Female' }].map((g) => (
                  <button key={g.label} type="button"
                    onClick={() => setGender(g.label as 'Male' | 'Female')}
                    className={`py-2 rounded-lg text-xs font-semibold border transition-all duration-200 ${
                      gender === g.label
                        ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}>
                    {g.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Weight</label>
                <span className="text-emerald-400 text-xs font-bold">{weight} kg</span>
              </div>
              <input type="range" min={30} max={200} value={weight}
                onChange={(e) => setWeight(Number(e.target.value))}
                className="w-full accent-emerald-500" />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Height</label>
                <span className="text-emerald-400 text-xs font-bold">{height} cm</span>
              </div>
              <input type="range" min={100} max={220} value={height}
                onChange={(e) => setHeight(Number(e.target.value))}
                className="w-full accent-emerald-500" />
            </div>

            <div className="flex items-center justify-between px-4 py-3 rounded-lg bg-slate-900/70 border border-slate-800">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Calculated BMI</span>
              <span className={`text-sm font-bold ${bmi < 18.5 ? 'text-sky-400' : bmi < 25 ? 'text-emerald-400' : bmi < 30 ? 'text-amber-400' : 'text-rose-400'}`}>
                {bmi} kg/m²
              </span>
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <div
                onClick={() => setIncludeShap(!includeShap)}
                className={`relative w-10 h-5 rounded-full transition-colors duration-200 ${includeShap ? 'bg-emerald-500' : 'bg-slate-700'}`}
              >
                <div className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${includeShap ? 'translate-x-5' : ''}`} />
              </div>
              <span className="text-xs text-slate-300">Generate SHAP explaining factors</span>
            </label>

            <button type="submit" disabled={loading}
              className="w-full py-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20 mt-2">
              {loading
                ? <span className="flex items-center justify-center gap-2"><span className="h-4 w-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />Analyzing Profile...</span>
                : 'Analyze My Diet'}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
              {error}
            </div>
          )}
        </div>

        {/* History / Previous Assessments List */}
        <div className="glass-panel rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-900">
            <h3 className="font-bold text-slate-200 text-xs flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-indigo-400" /> Past Checkups List
            </h3>
          </div>
          <div className="divide-y divide-slate-900/60 max-h-[300px] overflow-y-auto">
            {history.length === 0 ? (
              <p className="p-6 text-xs text-slate-500 text-center">No assessments found.</p>
            ) : (
              history.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectHistory(item)}
                  className="p-4 flex justify-between items-center hover:bg-white/[0.01] transition-colors cursor-pointer text-xs group"
                >
                  <div>
                    <p className="font-bold text-slate-300">
                      Checkup: {new Date(item.prediction_date).toLocaleDateString()}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      Max risk: {Math.round(Math.max(item.iron_risk, item.calcium_risk, item.vitamin_d_risk, item.vitamin_b12_risk, item.zinc_risk) * 100)}%
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-slate-400 transition-colors" />
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* ── RIGHT PANEL: Results, SHAP and recommendations (col-span-8) ── */}
      <div className="lg:col-span-8 space-y-6">
        {!results ? (
          <div className="glass-panel p-14 rounded-xl text-center flex flex-col items-center justify-center min-h-[500px]">
            <Activity className="h-16 w-16 text-slate-700 mb-4 animate-pulse" />
            <h4 className="text-slate-400 font-semibold text-base">Awaiting Diagnostic Metrics</h4>
            <p className="text-xs text-slate-600 max-w-sm mt-2 leading-relaxed">
              Configure parameters on the left and click Analyze My Diet to calculate real-time risks, SHAP features, and personalized recommendations.
            </p>
          </div>
        ) : (
          <>
            {/* Risk Levels Card Grid */}
            <div className="glass-panel p-6 rounded-xl">
              <h3 className="font-bold text-slate-200 text-sm mb-4 flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                Dietary Deficiency Assessment Results
                <span className="ml-auto text-[10px] text-slate-500 font-normal">Click a card to filter SHAP</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {NUTRIENTS.map(({ key, label }) =>
                  results.results[key]
                    ? renderRiskCard(key, label, results.results[key])
                    : null
                )}
              </div>
            </div>

            {/* Personalized Recommendations Panel */}
            {results.recommendations && (
              <div className="glass-panel p-6 rounded-xl space-y-6">
                <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2 border-b border-slate-900 pb-3">
                  <Apple className="h-5 w-5 text-emerald-400" /> Personalized Recommendations
                </h3>

                {/* Health Advice Callout */}
                <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs leading-relaxed flex items-start gap-2.5">
                  <Info className="h-4.5 w-4.5 mt-0.5 shrink-0 text-emerald-400" />
                  <div>
                    <span className="font-bold block mb-0.5">Clinical Wellness Advice</span>
                    {results.recommendations.short_health_advice}
                  </div>
                </div>

                {/* Foods to Eat (Static + DB foods mapped) */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                    <Utensils className="h-4 w-4 text-emerald-400" /> Nutrient-Dense Foods to Eat (per 100g)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {results.recommendations.foods_to_eat.map((food: RecommendationFoodItem, idx: number) => (
                      <div key={idx} className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
                        <span className="text-xs font-bold text-slate-200 truncate mb-1">{food.food_name}</span>
                        <span className="text-base font-extrabold text-emerald-400 mt-1">
                          {food.nutrient_amount.toFixed(1)} <span className="text-[10px] font-normal text-slate-500">{food.unit}</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Foods to Avoid & Nutrient Targets in 2 cols */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* Foods to Avoid list */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                      <XCircle className="h-4 w-4 text-rose-500" /> Foods / Habits to Avoid
                    </h4>
                    <ul className="space-y-2.5">
                      {results.recommendations.foods_to_avoid.map((item: string, idx: number) => (
                        <li key={idx} className="p-3 rounded-lg bg-rose-500/5 border border-rose-500/20 text-[11px] text-rose-300 leading-normal">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Recommended Daily Targets (RDA) */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                      <Target className="h-4 w-4 text-indigo-400" /> Recommended Daily Targets (RDA)
                    </h4>
                    <div className="rounded-lg border border-slate-800 overflow-hidden text-xs">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-900 text-slate-400 uppercase tracking-wider text-[9px] border-b border-slate-800">
                            <th className="py-2.5 px-4 font-semibold">Nutrient</th>
                            <th className="py-2.5 px-4 font-semibold text-right">RDA Target</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 text-slate-300">
                          {results.recommendations.daily_nutrient_targets.map((tgt: NutrientTarget, idx: number) => (
                            <tr key={idx} className="hover:bg-white/[0.01]">
                              <td className="py-2.5 px-4 font-medium">{tgt.nutrient}</td>
                              <td className="py-2.5 px-4 text-right font-bold text-indigo-400">
                                {tgt.target_value} <span className="text-[10px] font-normal text-slate-500">{tgt.unit}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

              </div>
            )}

            {/* Explanatory SHAP Panel */}
            {includeShap && activeShapData.length > 0 && (
              <div className="glass-panel p-6 rounded-xl">
                <h3 className="font-bold text-slate-200 text-sm mb-1 flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-indigo-400" />
                  SHAP Factor Analysis
                  <span className="ml-auto text-xs text-slate-500 font-normal capitalize">
                    {NUTRIENTS.find(n => n.key === activeShap)?.label} Deficiency
                  </span>
                </h3>
                <p className="text-xs text-slate-500 mb-5 leading-normal">
                  Values indicate risk contributions. Red bars increase risk, Green bars lower risk.
                </p>

                <div className="space-y-3.5">
                  {activeShapData.map((item) => {
                    const isPos    = item.contribution > 0;
                    const absPct   = Math.min(Math.abs(item.contribution) * 250, 50);
                    const label    = item.feature.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

                    return (
                      <div key={item.feature} className="grid grid-cols-12 items-center gap-3">
                        <div className="col-span-4">
                          <p className="text-xs font-semibold text-slate-200 truncate">{label}</p>
                          <p className="text-[10px] text-slate-600 mt-0.5">Value: {item.value.toFixed(1)}</p>
                        </div>

                        {/* Bidirectional bar chart indicator */}
                        <div className="col-span-6">
                          <div className="relative h-4.5 bg-slate-900 rounded overflow-hidden">
                            <div className="absolute top-0 bottom-0 left-1/2 w-px bg-slate-700" />
                            <div
                              className={`absolute top-1 bottom-1 rounded transition-all duration-500 ${isPos ? 'bg-rose-500/70' : 'bg-emerald-500/70'}`}
                              style={{
                                width: `${absPct}%`,
                                left:  isPos ? '50%' : undefined,
                                right: !isPos ? '50%' : undefined,
                              }}
                            />
                          </div>
                        </div>

                        <div className="col-span-2 text-right">
                          <span className={`text-xs font-mono font-bold ${isPos ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {isPos ? '+' : ''}{item.contribution.toFixed(3)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Predict;
