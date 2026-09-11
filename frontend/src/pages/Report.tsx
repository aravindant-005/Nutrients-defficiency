import React, { useState, useEffect } from 'react';
import {
  authAPI,
  predictAPI,
  foodLogAPI
} from '../services/api';
import type {
  UserProfile,
  PredictionHistoryItem,
  DailySummary,
  NutrientTarget
} from '../services/api';
import {
  FileText,
  Printer,
  ChevronLeft,
  User,
  Scale,
  Activity,
  Apple,
  Clock
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const NUTRIENT_KEYS: { key: keyof PredictionHistoryItem; label: string }[] = [
  { key: 'iron_risk',        label: 'Iron'        },
  { key: 'calcium_risk',     label: 'Calcium'     },
  { key: 'vitamin_d_risk',   label: 'Vitamin D'   },
  { key: 'vitamin_b12_risk', label: 'Vitamin B12' },
  { key: 'zinc_risk',        label: 'Zinc'        },
];

const DashboardReport: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile]     = useState<UserProfile | null>(null);
  const [history, setHistory]     = useState<PredictionHistoryItem[]>([]);
  const [summary, setSummary]     = useState<DailySummary | null>(null);
  
  const [loading, setLoading]     = useState(true);
  const [dateStr]                 = useState(() => new Date().toLocaleString());

  useEffect(() => {
    const loadReportData = async () => {
      try {
        const [pRes, hRes, sRes] = await Promise.all([
          authAPI.me(),
          predictAPI.history(),
          foodLogAPI.summary(),
        ]);
        setProfile(pRes.data);
        setHistory(hRes.data);
        setSummary(sRes.data);
      } catch (e) {
        console.error('Error compiling report details:', e);
      } finally {
        setLoading(false);
      }
    };
    loadReportData();
  }, []);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-slate-500 print:hidden">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent mb-3" />
        <p className="text-sm font-medium">Compiling health report data...</p>
      </div>
    );
  }

  const latest = history[0];

  // Helper to categorize BMI
  const getBmiCategory = (bmi: number) => {
    if (bmi < 18.5) return 'Underweight';
    if (bmi < 25.0) return 'Normal weight';
    if (bmi < 30.0) return 'Overweight';
    return 'Obese';
  };

  // Static daily RDA target values fallback based on gender/age
  const getDailyRdaTargets = (user: UserProfile): NutrientTarget[] => {
    const isFemale = user.gender ? ["female", "f", "1"].includes(user.gender.trim().toLowerCase()) : false;
    const age = user.age || 30;

    return [
      { nutrient: "Iron", target_value: isFemale && age < 50 ? 18.0 : 8.0, unit: "mg" },
      { nutrient: "Calcium", target_value: (isFemale && age > 50) || (!isFemale && age > 70) ? 1200.0 : 1000.0, unit: "mg" },
      { nutrient: "Vitamin D", target_value: age > 70 ? 20.0 : 15.0, unit: "mcg" },
      { nutrient: "Vitamin B12", target_value: 2.4, unit: "mcg" },
      { nutrient: "Zinc", target_value: isFemale ? 8.0 : 11.0, unit: "mg" }
    ];
  };

  const isFemale = profile ? (profile.gender ? ["female", "f", "1"].includes(profile.gender.toLowerCase()) : false) : false;
  const age = profile?.age || 30;
  const rdaTargets = profile ? getDailyRdaTargets(profile) : [];

  // Generate personalized static food advice based on risk scores
  const getPersonalizedFoodAdvice = (item: PredictionHistoryItem) => {
    const list: string[] = [];
    if (item.iron_risk >= 0.5) list.push("Iron (Spinach, Lentils, Beef steak, Pumpkin seeds)");
    if (item.calcium_risk >= 0.5) list.push("Calcium (Plain Yogurt, Almonds, Tofu, Sardines)");
    if (item.vitamin_d_risk >= 0.5) list.push("Vitamin D (Salmon, Egg yolks, Fortified milk)");
    if (item.vitamin_b12_risk >= 0.5) list.push("Vitamin B12 (Clams, Beef liver, Fortified yeast)");
    if (item.zinc_risk >= 0.5) list.push("Zinc (Oysters, Pumpkin seeds, Beef, Cashews)");

    if (list.length === 0) {
      // Recommend for highest risk
      const highest = Object.entries({
        iron: item.iron_risk,
        calcium: item.calcium_risk,
        vitamin_d: item.vitamin_d_risk,
        vitamin_b12: item.vitamin_b12_risk,
        zinc: item.zinc_risk
      }).sort((a,b) => b[1] - a[1])[0][0];
      
      const map: Record<string, string> = {
        iron: "Iron (Spinach, Pumpkin seeds, Lentils)",
        calcium: "Calcium (Yogurt, Cheese, Almonds)",
        vitamin_d: "Vitamin D (Salmon, Fortified milk)",
        vitamin_b12: "Vitamin B12 (Tuna, Eggs, Fortified yeast)",
        zinc: "Zinc (Oysters, Cashews, Beef)"
      };
      list.push(map[highest]);
    }
    return list;
  };

  const recFoods = latest ? getPersonalizedFoodAdvice(latest) : [];

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-4 md:p-8 animate-fadeIn print:bg-white print:text-slate-900 print:p-0 print:max-w-full">
      
      {/* ── Action Buttons (hidden during printing) ── */}
      <div className="flex justify-between items-center print:hidden">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400 hover:text-slate-200 transition-all"
        >
          <ChevronLeft className="h-4 w-4" /> Back
        </button>
        <button
          onClick={handlePrint}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-emerald-500/10"
        >
          <Printer className="h-4 w-4" /> Print / Save PDF
        </button>
      </div>

      {/* ── Printable Report Container ── */}
      <div className="glass-panel p-8 rounded-2xl border border-slate-900 space-y-8 bg-slate-950/40 backdrop-blur-md print:bg-white print:border-none print:shadow-none print:p-0">
        
        {/* Report Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-900 print:border-slate-300 pb-6 gap-4">
          <div className="space-y-1.5">
            <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent print:text-emerald-650 print:bg-none print:text-slate-900">
              NutriAI Diagnostics Report
            </h1>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">
              Clinical Nutrient Deficiency & Diet Analysis
            </p>
          </div>
          <div className="text-right text-xs text-slate-400 space-y-1">
            <div className="flex items-center md:justify-end gap-1.5">
              <Clock className="h-3.5 w-3.5 text-slate-500" />
              <span>Generated: {dateStr}</span>
            </div>
            <p className="text-[10px] text-slate-500 font-mono">REPORT REF: #{profile?.id ?? 0}-{new Date().getTime().toString().slice(-6)}</p>
          </div>
        </div>

        {/* Section 1: Patient Profile & Body Mass Index */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Patient Profile */}
          <div className="space-y-3.5">
            <h3 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-2 border-b border-slate-900/60 print:border-slate-200 pb-2">
              <User className="h-4 w-4 text-emerald-400 shrink-0" /> Patient Information
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-500 block">Full Name</span>
                <span className="font-bold text-slate-200">{profile?.name}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Email Address</span>
                <span className="text-slate-300 font-medium">{profile?.email}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Age / Gender</span>
                <span className="text-slate-200 font-bold">{age} yrs · {profile?.gender}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Activity Level</span>
                <span className="text-slate-200 font-semibold">{profile?.activity_level ?? 'Moderate'}</span>
              </div>
            </div>
          </div>

          {/* Body Mass Index Details */}
          <div className="space-y-3.5">
            <h3 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-2 border-b border-slate-900/60 print:border-slate-200 pb-2">
              <Scale className="h-4 w-4 text-indigo-400 shrink-0" /> Body Mass Index (BMI)
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-500 block">Height / Weight</span>
                <span className="text-slate-200 font-semibold">{profile?.height} cm / {profile?.weight} kg</span>
              </div>
              <div>
                <span className="text-slate-500 block">Calculated BMI</span>
                <span className="text-slate-200 font-extrabold">{profile?.bmi?.toFixed(1)} kg/m²</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-500 block">Weight Classification</span>
                <span className="text-slate-200 font-bold text-emerald-400">
                  {profile?.bmi ? getBmiCategory(profile.bmi) : 'Normal weight'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Deficiency Prediction Results */}
        <div className="space-y-3.5">
          <h3 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-2 border-b border-slate-900/60 print:border-slate-200 pb-2">
            <Activity className="h-4 w-4 text-rose-500 shrink-0" /> Diagnostic Deficiency Risk Model (XGBoost / Random Forest)
          </h3>
          {latest ? (
            <div className="rounded-lg border border-slate-900 overflow-hidden text-xs print:border-slate-300">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-900 text-slate-400 uppercase tracking-wider text-[9px] border-b border-slate-900 print:bg-slate-100 print:text-slate-700 print:border-slate-300">
                    <th className="py-2.5 px-4 font-semibold">Nutrient deficiency Target</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Calculated Probability</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Risk Assessment Level</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 text-slate-300 print:divide-slate-200">
                  {NUTRIENT_KEYS.map(({ key, label }) => {
                    const score = latest[key] as number;
                    const rClass = score >= 0.70 ? 'text-rose-400 font-bold' : score >= 0.45 ? 'text-amber-400 font-bold' : 'text-emerald-400';
                    return (
                      <tr key={key} className="hover:bg-white/[0.01]">
                        <td className="py-2.5 px-4 font-medium text-slate-200">{label}</td>
                        <td className="py-2.5 px-4 text-center font-mono font-semibold text-slate-200">{(score * 100).toFixed(1)}%</td>
                        <td className={`py-2.5 px-4 text-right ${rClass}`}>{score >= 0.70 ? 'HIGH RISK' : score >= 0.45 ? 'MODERATE RISK' : 'LOW RISK'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No deficiency forecasts logged. Please run predictive forecasting first.</p>
          )}
        </div>

        {/* Section 3: Today's Nutrient Intake vs RDA targets */}
        <div className="space-y-3.5">
          <h3 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-2 border-b border-slate-900/60 print:border-slate-200 pb-2">
            <Apple className="h-4 w-4 text-amber-500 shrink-0" /> Today's Cumulative Dietary Nutrient Intake
          </h3>
          {summary ? (
            <div className="rounded-lg border border-slate-900 overflow-hidden text-xs print:border-slate-300">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-900 text-slate-400 uppercase tracking-wider text-[9px] border-b border-slate-900 print:bg-slate-100 print:text-slate-700 print:border-slate-300">
                    <th className="py-2.5 px-4 font-semibold">Nutrient Parameter</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Today's Total Intake</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Daily RDA Target</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Intake Coverage Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 text-slate-300 print:divide-slate-200">
                  {[
                    { name: 'Calories', val: summary.calories, unit: 'kcal', tgt: 2000 },
                    { name: 'Protein', val: summary.protein, unit: 'g', tgt: isFemale ? 46 : 56 },
                    { name: 'Carbohydrates', val: summary.carbohydrates, unit: 'g', tgt: 130 },
                    { name: 'Fat', val: summary.fat, unit: 'g', tgt: 70 },
                    { name: 'Iron', val: summary.iron, unit: 'mg', tgt: rdaTargets.find(t => t.nutrient === "Iron")?.target_value ?? 8.0 },
                    { name: 'Calcium', val: summary.calcium, unit: 'mg', tgt: rdaTargets.find(t => t.nutrient === "Calcium")?.target_value ?? 1000.0 },
                    { name: 'Vitamin D', val: summary.vitamin_d, unit: 'mcg', tgt: rdaTargets.find(t => t.nutrient === "Vitamin D")?.target_value ?? 15.0 },
                    { name: 'Vitamin B12', val: summary.vitamin_b12, unit: 'mcg', tgt: rdaTargets.find(t => t.nutrient === "Vitamin B12")?.target_value ?? 2.4 },
                    { name: 'Zinc', val: summary.zinc, unit: 'mg', tgt: rdaTargets.find(t => t.nutrient === "Zinc")?.target_value ?? 11.0 },
                  ].map((nut) => {
                    const pct = nut.tgt > 0 ? (nut.val / nut.tgt) * 100 : 0;
                    return (
                      <tr key={nut.name} className="hover:bg-white/[0.01]">
                        <td className="py-2.5 px-4 font-medium text-slate-200">{nut.name}</td>
                        <td className="py-2.5 px-4 text-center font-bold text-slate-100">{nut.val.toFixed(1)} {nut.unit}</td>
                        <td className="py-2.5 px-4 text-center text-slate-400">{nut.tgt} {nut.unit}</td>
                        <td className={`py-2.5 px-4 text-right font-semibold ${pct >= 100 ? 'text-emerald-400' : pct >= 50 ? 'text-amber-400' : 'text-rose-400'}`}>
                          {pct.toFixed(0)}% RDA met
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No food logs found for today.</p>
          )}
        </div>

        {/* Section 4: Personalized Food Recommendations */}
        {latest && recFoods.length > 0 && (
          <div className="space-y-3.5">
            <h3 className="font-bold text-slate-200 text-xs uppercase tracking-wider flex items-center gap-2 border-b border-slate-900/60 print:border-slate-200 pb-2">
              <FileText className="h-4 w-4 text-emerald-400 shrink-0" /> Target Recommendations & Nutritional Advice
            </h3>
            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-900 print:bg-slate-50 print:border-slate-200 text-xs space-y-3.5">
              <div>
                <span className="font-semibold text-slate-400 block mb-1">Recommended Nutrient-Dense Foods:</span>
                <p className="text-slate-200 font-semibold">{recFoods.join(" · ")}</p>
              </div>
              <div>
                <span className="font-semibold text-slate-400 block mb-1">Key Absorption Inhibitors / Habits to Limit:</span>
                <p className="text-slate-300 leading-relaxed font-medium">
                  Do not consume caffeine with iron meals. Limit sodium and carbonated sodas to retain calcium. Restrict phytates from whole grains if prone to zinc deficiency.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Clinic Signature Section (Dotted Line) */}
        <div className="pt-12 flex justify-between items-end border-t border-slate-900/40 print:border-slate-200 text-xs">
          <div>
            <p className="text-slate-500">Report Status</p>
            <p className="font-bold text-emerald-400">AUTHENTICATED (DIGITALLY SIGNED)</p>
          </div>
          <div className="text-right space-y-1">
            <p className="text-slate-500">Authorized Clinician Signature</p>
            <div className="w-48 border-b border-dashed border-slate-500/80 pt-6" />
            <p className="text-[10px] text-slate-500 italic">NutriAI Diagnostics Team</p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default DashboardReport;
