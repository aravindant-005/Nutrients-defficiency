import React, { useState, useEffect, useTransition } from 'react';
import { foodLogAPI, foodCatalogAPI, parseApiError } from '../services/api';
import type { FoodLogItem, DailySummary, FoodLogCreate, FoodCatalogItem } from '../services/api';
import {
  UtensilsCrossed,
  Trash2,
  Calendar,
  Flame,
  Beef,
  Droplets,
  Zap,
  Search,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  Check
} from 'lucide-react';

const MEAL_TYPES = ['Breakfast', 'Lunch', 'Dinner', 'Snack'] as const;

const MEAL_COLORS: Record<string, string> = {
  Breakfast: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  Lunch:     'text-sky-400   bg-sky-500/10   border-sky-500/30',
  Dinner:    'text-violet-400 bg-violet-500/10 border-violet-500/30',
  Snack:     'text-rose-400  bg-rose-500/10  border-rose-500/30',
};

const FoodLog: React.FC = () => {
  const todayStr = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(todayStr);
  const [logs, setLogs] = useState<FoodLogItem[]>([]);
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Custom manual logging state
  const [customFormOpen, setCustomFormOpen] = useState(false);
  const [customForm, setCustomForm] = useState<FoodLogCreate>({
    food_name: '', quantity: 100, serving_size: 'g', meal_type: 'Breakfast',
    calories: 0, protein: 0, carbohydrates: 0, fat: 0,
    iron: 0, calcium: 0, vitamin_d: 0, vitamin_b12: 0, zinc: 0
  });

  // Food catalog search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FoodCatalogItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedFood, setSelectedFood]   = useState<FoodCatalogItem | null>(null);
  
  // Logging parameters for catalog item
  const [logMealType, setLogMealType] = useState<'Breakfast' | 'Lunch' | 'Dinner' | 'Snack'>('Breakfast');
  const [logQuantity, setLogQuantity] = useState<number>(100);
  
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [isPending, startTransition] = useTransition();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [logsRes, summaryRes] = await Promise.all([
        foodLogAPI.list(date),
        foodLogAPI.summary(date),
      ]);
      setLogs(logsRes.data);
      setSummary(summaryRes.data);
    } catch (e) {
      console.error('Error fetching logs:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [date]);

  // Handle live food catalog search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || searchQuery.trim().length < 2) return;
    
    setSearchLoading(true);
    setSelectedFood(null);
    try {
      const { data } = await foodCatalogAPI.search(searchQuery);
      setSearchResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSearchLoading(false);
    }
  };

  // Log a food item selected from the catalog
  const handleLogCatalogItem = async () => {
    if (!selectedFood) return;
    setSubmitting(true);
    setErrorMessage(null);

    // Calculate nutrients proportionally based on selected logging quantity (relative to 100g standard)
    const factor = logQuantity / 100.0;
    
    const payload: FoodLogCreate = {
      food_name: selectedFood.food_name,
      quantity: logQuantity,
      serving_size: 'g',
      meal_type: logMealType,
      calories: (selectedFood.calories_kcal ?? 0) * factor,
      protein: (selectedFood.protein_g ?? 0) * factor,
      carbohydrates: (selectedFood.carbs_g ?? 0) * factor,
      fat: (selectedFood.fat_g ?? 0) * factor,
      iron: (selectedFood.iron_mg ?? 0) * factor,
      calcium: (selectedFood.calcium_mg ?? 0) * factor,
      vitamin_d: (selectedFood.vitamin_d_mcg ?? 0) * factor,
      vitamin_b12: (selectedFood.vitamin_b12_mcg ?? 0) * factor,
      zinc: (selectedFood.zinc_mg ?? 0) * factor,
    };

    try {
      await foodLogAPI.create(payload);
      setSelectedFood(null);
      setSearchQuery('');
      setSearchResults([]);
      fetchData();
    } catch (err: any) {
      setErrorMessage(parseApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  // Handle custom customForm submission
  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);
    try {
      await foodLogAPI.create(customForm);
      setCustomForm({
        food_name: '', quantity: 100, serving_size: 'g', meal_type: 'Breakfast',
        calories: 0, protein: 0, carbohydrates: 0, fat: 0,
        iron: 0, calcium: 0, vitamin_d: 0, vitamin_b12: 0, zinc: 0
      });
      setCustomFormOpen(false);
      fetchData();
    } catch (err: any) {
      setErrorMessage(parseApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    await foodLogAPI.delete(id);
    fetchData();
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400">
            <UtensilsCrossed className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-200">Nutrition & Food Log</h2>
            <p className="text-xs text-slate-500">Track and monitor your nutrient goals</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800">
            <Calendar className="h-4 w-4 text-slate-400" />
            <input
              type="date"
              value={date}
              onChange={(e) => startTransition(() => setDate(e.target.value))}
              className="bg-transparent text-sm text-slate-200 focus:outline-none"
            />
          </div>
          <button
            onClick={() => setCustomFormOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-semibold text-sm hover:border-slate-700 transition-all"
          >
            Custom Entry
          </button>
        </div>
      </div>

      {/* ── Daily Summary Cards ── */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Calories', value: summary.calories, unit: 'kcal', icon: Flame,    color: 'amber'   },
            { label: 'Protein',  value: summary.protein,  unit: 'g',    icon: Beef,     color: 'rose'    },
            { label: 'Carbs',    value: summary.carbohydrates, unit: 'g', icon: Zap,    color: 'sky'     },
            { label: 'Fat',      value: summary.fat,       unit: 'g',    icon: Droplets, color: 'violet'  },
          ].map(({ label, value, unit, icon: Icon, color }) => (
            <div key={label} className="glass-panel p-4 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-xl font-bold text-slate-200 mt-1">
                  {value.toFixed(0)} <span className="text-xs font-normal text-slate-500">{unit}</span>
                </p>
              </div>
              <div className={`p-3 rounded-lg bg-${color}-500/10 text-${color}-450`}>
                <Icon className="h-5 w-5" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Core Section: Search Catalog & Recent Logs ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Panel: Food search from catalog */}
        <div className="lg:col-span-6 space-y-4">
          <div className="glass-panel p-6 rounded-xl space-y-5">
            <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-emerald-400" /> Search Food Database
            </h3>
            
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search spinach, salmon, beef..."
                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:border-emerald-500"
              />
              <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
              <button
                type="submit"
                className="absolute right-2 top-2 px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 font-semibold"
              >
                Go
              </button>
            </form>

            {/* Live Search results list */}
            {searchLoading ? (
              <div className="text-center py-8 text-slate-500">
                <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent mr-2" />
                Searching database...
              </div>
            ) : searchResults.length > 0 ? (
              <div className="max-h-[300px] overflow-y-auto space-y-2 pr-1">
                {searchResults.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => setSelectedFood(item)}
                    className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                      selectedFood?.id === item.id
                        ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-300'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                    }`}
                  >
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-200">{item.food_name}</span>
                      <ArrowRight className="h-3.5 w-3.5 text-slate-600" />
                    </div>
                  </div>
                ))}
              </div>
            ) : searchQuery.length >= 2 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No results found in food catalog.</p>
            ) : null}

            {/* Catalog Log Configurator */}
            {selectedFood && (
              <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800/80 space-y-4 animate-fadeIn">
                <div className="border-b border-slate-800/50 pb-2">
                  <h4 className="font-bold text-slate-200 text-xs truncate">{selectedFood.food_name}</h4>
                  <span className="text-[10px] text-slate-500">USDA standard reference values per 100g</span>
                </div>

                {/* Nutrient values list */}
                <div className="grid grid-cols-3 gap-3 text-center">
                  {[
                    { label: 'Calories', val: selectedFood.calories_kcal, unit: 'kcal' },
                    { label: 'Protein', val: selectedFood.protein_g, unit: 'g' },
                    { label: 'Carbs', val: selectedFood.carbs_g, unit: 'g' },
                    { label: 'Fat', val: selectedFood.fat_g, unit: 'g' },
                    { label: 'Iron', val: selectedFood.iron_mg, unit: 'mg' },
                    { label: 'Calcium', val: selectedFood.calcium_mg, unit: 'mg' },
                    { label: 'Vit D', val: selectedFood.vitamin_d_mcg, unit: 'mcg' },
                    { label: 'Vit B12', val: selectedFood.vitamin_b12_mcg, unit: 'mcg' },
                    { label: 'Zinc', val: selectedFood.zinc_mg, unit: 'mg' },
                  ].map((nut) => (
                    <div key={nut.label} className="p-2 bg-slate-950/40 border border-slate-900 rounded-lg">
                      <span className="text-[9px] text-slate-500 uppercase tracking-wider block">{nut.label}</span>
                      <span className="text-xs font-bold text-slate-200">{nut.val?.toFixed(2) ?? 0.0}</span>
                      <span className="text-[8px] text-slate-600 block">{nut.unit}</span>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase block mb-1">Serving (grams)</label>
                    <input
                      type="number"
                      min={10}
                      max={1000}
                      value={logQuantity}
                      onChange={(e) => setLogQuantity(parseFloat(e.target.value) || 100)}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-900 text-slate-200 text-xs focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 uppercase block mb-1">Meal category</label>
                    <select
                      value={logMealType}
                      onChange={(e) => setLogMealType(e.target.value as any)}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-900 text-slate-200 text-xs focus:outline-none"
                    >
                      {MEAL_TYPES.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {errorMessage && <p className="text-rose-400 text-xs">{errorMessage}</p>}

                <button
                  onClick={handleLogCatalogItem}
                  disabled={submitting}
                  className="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all flex items-center justify-center gap-2"
                >
                  <Check className="h-4 w-4" /> {submitting ? 'Logging...' : 'Add Meal Entry'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: food logs summary */}
        <div className="lg:col-span-6 space-y-4">
          <div className="glass-panel rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-900">
              <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
                <UtensilsCrossed className="h-4 w-4 text-indigo-400" />
                Logged Items — {new Date(date).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
              </h3>
            </div>

            {loading || isPending ? (
              <div className="p-12 text-center text-slate-500">
                <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent mb-3" />
                <p className="text-xs">Loading logs...</p>
              </div>
            ) : logs.length === 0 ? (
              <div className="p-14 text-center text-slate-500 flex flex-col items-center justify-center min-h-[300px]">
                <UtensilsCrossed className="h-12 w-12 text-slate-800 mb-3" />
                <p className="text-xs">No food logs submitted for this day.</p>
                <p className="text-[10px] text-slate-600 mt-1">Search the database on the left to get started.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-900/50">
                {logs.map((log) => (
                  <div key={log.id} className="px-6 py-4 flex items-center gap-4 hover:bg-white/[0.01] transition-colors">
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border shrink-0 ${MEAL_COLORS[log.meal_type]}`}>
                      {log.meal_type}
                    </span>

                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-slate-200 truncate">{log.food_name}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {log.quantity}{log.serving_size} · {log.calories?.toFixed(0)} kcal · 
                        Iron: {log.iron?.toFixed(1)}mg · Calcium: {log.calcium?.toFixed(0)}mg ·
                        Vit D: {log.vitamin_d?.toFixed(1)}mcg
                      </p>
                    </div>

                    <button
                      onClick={() => handleDelete(log.id)}
                      className="text-slate-700 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/10 transition-all shrink-0"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* ── Custom Entry Modal ── */}
      {customFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="glass-panel rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="font-bold text-slate-200 text-sm mb-4">Log Custom Food Item</h3>
            <form onSubmit={handleCustomSubmit} className="space-y-4">
              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Food Name *</label>
                <input
                  required
                  value={customForm.food_name}
                  onChange={(e) => setCustomForm({ ...customForm, food_name: e.target.value })}
                  placeholder="e.g. Oatmeal with berries"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-slate-500 uppercase block mb-1">Quantity *</label>
                  <input
                    type="number"
                    required
                    min={0}
                    value={customForm.quantity}
                    onChange={(e) => setCustomForm({ ...customForm, quantity: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 uppercase block mb-1">Serving unit *</label>
                  <input
                    value={customForm.serving_size}
                    onChange={(e) => setCustomForm({ ...customForm, serving_size: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Meal category *</label>
                <div className="grid grid-cols-4 gap-2">
                  {MEAL_TYPES.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setCustomForm({ ...customForm, meal_type: m })}
                      className={`py-1.5 rounded-lg text-[10px] font-semibold border transition-all ${
                        customForm.meal_type === m ? MEAL_COLORS[m] : 'bg-slate-900 border-slate-800 text-slate-500'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider pt-2 border-t border-slate-900/60">Nutritional Facts</p>
              
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Calories (kcal)', key: 'calories' },
                  { label: 'Protein (g)', key: 'protein' },
                  { label: 'Carbs (g)', key: 'carbohydrates' },
                  { label: 'Fat (g)', key: 'fat' },
                  { label: 'Iron (mg)', key: 'iron' },
                  { label: 'Calcium (mg)', key: 'calcium' },
                  { label: 'Vitamin D (mcg)', key: 'vitamin_d' },
                  { label: 'Vitamin B12 (mcg)', key: 'vitamin_b12' },
                  { label: 'Zinc (mg)', key: 'zinc' },
                ].map((nut) => (
                  <div key={nut.key}>
                    <label className="text-[9px] text-slate-500 block mb-0.5">{nut.label}</label>
                    <input
                      type="number"
                      min={0}
                      step={0.1}
                      value={(customForm[nut.key as keyof FoodLogCreate] as number) ?? 0}
                      onChange={(e) => setCustomForm({ ...customForm, [nut.key]: parseFloat(e.target.value) || 0 })}
                      className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-200 text-xs focus:outline-none"
                    />
                  </div>
                ))}
              </div>

              {errorMessage && <p className="text-rose-400 text-xs">{errorMessage}</p>}

              <div className="flex gap-3 pt-3 border-t border-slate-900/65">
                <button
                  type="button"
                  onClick={() => { setCustomFormOpen(false); setErrorMessage(null); }}
                  className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold flex items-center justify-center gap-1.5"
                >
                  <ShieldCheck className="h-4 w-4" /> {submitting ? 'Saving...' : 'Save Log'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default FoodLog;
