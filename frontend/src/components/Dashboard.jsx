import React from 'react';
import { Zap, Flame, ShieldAlert, ArrowUpRight, CheckCircle2, AlertTriangle, PlusCircle } from 'lucide-react';

export default function Dashboard({ dailyData, onNavigate }) {
  if (!dailyData) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading Dashboard Data...</div>;
  }

  const { daily_totals, rda_targets, logs } = dailyData;

  const macros = [
    { label: 'Calories', val: daily_totals.calories_kcal, target: 2000, unit: 'kcal', color: '#06b6d4', icon: Flame },
    { label: 'Protein', val: daily_totals.protein_g, target: 65, unit: 'g', color: '#10b981', icon: Zap },
    { label: 'Carbohydrates', val: daily_totals.carbs_g, target: 250, unit: 'g', color: '#f59e0b', icon: Zap },
    { label: 'Fat', val: daily_totals.fat_g, target: 60, unit: 'g', color: '#818cf8', icon: Zap },
    { label: 'Fiber', val: daily_totals.fiber_g, target: 30, unit: 'g', color: '#ec4899', icon: Zap },
  ];

  const micros = [
    { key: 'iron_mg', label: 'Iron', val: daily_totals.iron_mg, target: rda_targets.iron || 18, unit: 'mg' },
    { key: 'calcium_mg', label: 'Calcium', val: daily_totals.calcium_mg, target: rda_targets.calcium || 1000, unit: 'mg' },
    { key: 'vitamin_d_mcg', label: 'Vitamin D', val: daily_totals.vitamin_d_mcg, target: rda_targets.vitamin_d || 15, unit: 'mcg' },
    { key: 'vitamin_b12_mcg', label: 'Vitamin B12', val: daily_totals.vitamin_b12_mcg, target: rda_targets.vitamin_b12 || 2.4, unit: 'mcg' },
    { key: 'zinc_mg', label: 'Zinc', val: daily_totals.zinc_mg, target: rda_targets.zinc || 11, unit: 'mg' },
    { key: 'magnesium_mg', label: 'Magnesium', val: daily_totals.magnesium_mg, target: rda_targets.magnesium || 400, unit: 'mg' },
    { key: 'vitamin_c_mg', label: 'Vitamin C', val: daily_totals.vitamin_c_mg, target: rda_targets.vitamin_c || 90, unit: 'mg' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Welcome Banner */}
      <div className="glass-panel" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.15))', border: '1px solid rgba(52, 211, 153, 0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '6px' }}>Daily Micronutrient Overview</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Real-time dietary intake tracking & RDA completion status for Indian Diets.</p>
          </div>
          <button className="btn-primary" onClick={() => onNavigate('logger')}>
            <PlusCircle size={18} />
            Log Today's Meals
          </button>
        </div>
      </div>

      {/* Macronutrient Cards */}
      <div>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Flame size={18} color="#06b6d4" />
          Macronutrient Totals
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {macros.map((m, idx) => {
            const pct = Math.min(100, Math.round((m.val / m.target) * 100));
            return (
              <div key={idx} className="glass-panel glass-panel-interactive" style={{ padding: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>{m.label}</span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: m.color }}>{pct}% RDA</span>
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '8px' }}>
                  {m.val} <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-dim)' }}>{m.unit}</span>
                </div>
                <div className="progress-bg">
                  <div className="progress-fill" style={{ width: `${pct}%`, background: m.color }}></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Micronutrient RDA Progress Bars & Recent Logs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>
        
        {/* Micronutrient RDA Gauges */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={18} color="#34d399" />
              Micronutrient RDA Status
            </h3>
            <button className="btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px' }} onClick={() => onNavigate('risk')}>
              Run ML Risk Check
              <ArrowUpRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {micros.map((micro, idx) => {
              const pct = Math.min(100, Math.round((micro.val / micro.target) * 100));
              let statusColor = '#34d399';
              if (pct < 40) statusColor = '#f87171';
              else if (pct < 70) statusColor = '#fbbf24';

              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 600 }}>{micro.label}</span>
                    <span style={{ color: 'var(--text-muted)' }}>
                      <strong style={{ color: statusColor }}>{micro.val}</strong> / {micro.target} {micro.unit} ({pct}%)
                    </span>
                  </div>
                  <div className="progress-bg">
                    <div className="progress-fill" style={{ width: `${pct}%`, background: statusColor }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Today's Logged Food Items Summary */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={18} color="#06b6d4" />
            Today's Meals ({logs.length} logged)
          </h3>

          {logs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 10px', color: 'var(--text-muted)' }}>
              <AlertTriangle size={32} color="var(--warning-amber)" style={{ marginBottom: '10px' }} />
              <p style={{ fontSize: '0.9rem', marginBottom: '12px' }}>No meals logged for today yet.</p>
              <button className="btn-primary" onClick={() => onNavigate('logger')}>Log Your First Meal</button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '380px', overflowY: 'auto' }}>
              {logs.map((item) => (
                <div key={item.id} style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.food_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Serving: {item.serving_size_g}g</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#38bdf8' }}>{item.calories_kcal} kcal</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Iron: {item.iron_mg}mg | Vit C: {item.vitamin_c_mg}mg</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
