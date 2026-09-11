import React, { useState } from 'react';
import axios from 'axios';
import { AlertTriangle, Play, Sparkles, Activity, Info, PlusCircle, AlertCircle, BookOpen, Layers } from 'lucide-react';

export default function RiskAnalysis({ userProfile, onNavigate }) {
  const [predData, setPredData] = useState(null);
  const [loading, setLoading] = useState(false);

  const runPrediction = async () => {
    setLoading(true);
    try {
      const uid = userProfile?.id || 1;
      const res = await axios.post(`/api/predict/risk/${uid}`);
      setPredData(res.data);
    } catch (err) {
      console.error('Prediction failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const hasLogged = predData ? predData.has_logged_data : true;
  const predictions = predData ? predData.predictions : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }} className="animate-fade-in">
      
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(244, 63, 94, 0.14), rgba(245, 158, 11, 0.14))', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase' }}>ML Models Engine</span>
            <h2 style={{ fontSize: '1.4rem', marginTop: '4px' }}>Micronutrient Deficiency Risk & SHAP Explainer</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Evaluates daily dietary totals + user health profile (Age {userProfile?.age}, BMI {userProfile?.bmi}) against trained models.
            </p>
          </div>
          <button className="btn-primary" style={{ background: 'linear-gradient(135deg, #f43f5e, #f59e0b)', boxShadow: '0 4px 14px rgba(244, 63, 94, 0.35)' }} onClick={runPrediction} disabled={loading}>
            {loading ? <Activity size={18} className="animate-spin" /> : <Play size={18} />}
            {loading ? 'Evaluating ML Models...' : 'Run ML Risk Prediction'}
          </button>
        </div>
      </div>

      {/* Scientific Methodology Explanation Card */}
      <div className="glass-panel" style={{ padding: '22px', border: '1px solid rgba(6, 182, 212, 0.3)', background: 'rgba(6, 182, 212, 0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#38bdf8', fontWeight: 700, fontSize: '0.95rem', marginBottom: '8px' }}>
          <BookOpen size={20} />
          Scientific Methodology: Single-Day Snapshot vs. Multi-Day Rolling Average ML Prediction
        </div>
        <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.55, margin: 0 }}>
          <strong>How Deficiency Calculation Works:</strong> Clinical nutrition recognizes that a single day's recall provides an acute snapshot baseline (<code style={{ color: '#34d399' }}>grpC_</code> and <code style={{ color: '#34d399' }}>grpD_</code> features). However, micronutrient deficiency is a <em>chronic condition</em>. Our feature engineering pipeline explicitly computes <strong>Group E Features (<code style={{ color: '#38bdf8' }}>grpE_mean</code>, <code style={{ color: '#38bdf8' }}>grpE_cv</code>)</strong> across your logged history in the <strong>Multi-Day History</strong> tab. Logging meals over <strong>3 to 7 days</strong> enables the ML model to evaluate rolling mean intake and dietary variability, producing high-confidence chronic deficiency risk scores!
        </p>
      </div>

      {/* 0-Log Validation State */}
      {predData && !hasLogged ? (
        <div className="glass-panel" style={{ padding: '50px', textAlign: 'center', borderColor: 'rgba(245, 158, 11, 0.4)' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <AlertCircle size={36} color="var(--warning-amber)" />
          </div>
          <h3 style={{ fontSize: '1.3rem', marginBottom: '8px' }}>No Food Logged for Today Yet!</h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto 20px auto', lineHeight: 1.5 }}>
            To run a scientifically accurate ML Deficiency Risk Analysis, you must first search and log your daily meals in the Food Logger tab.
          </p>
          <button className="btn-primary" onClick={() => onNavigate('logger')}>
            <PlusCircle size={18} />
            Go to Food Logger & Add Meals
          </button>
        </div>
      ) : !predictions ? (
        <div className="glass-panel" style={{ padding: '50px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Sparkles size={40} color="#06b6d4" style={{ marginBottom: '14px' }} />
          <h3 style={{ color: 'var(--text-main)', marginBottom: '8px' }}>No Risk Evaluation Generated Yet</h3>
          <p style={{ fontSize: '0.9rem', maxWidth: '520px', margin: '0 auto 20px auto' }}>
            Click "Run ML Risk Prediction" above to analyze your logged meals against trained machine learning models (`best_model_*.pkl`).
          </p>
          <button className="btn-primary" onClick={runPrediction}>Run Analysis Now</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          <h3 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="#06b6d4" />
            Nutrient Risk Assessment & Feature Attribution ({predictions.length} Targets)
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            {predictions.map((p, idx) => {
              let badgeClass = "badge-low";
              let progressColor = "#34d399";
              if (p.risk_level === "High Risk") {
                badgeClass = "badge-high";
                progressColor = "#f87171";
              } else if (p.risk_level === "Moderate Risk") {
                badgeClass = "badge-moderate";
                progressColor = "#fbbf24";
              }

              return (
                <div key={idx} className="glass-panel glass-panel-interactive" style={{ padding: '22px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <h4 style={{ fontSize: '1.15rem' }}>{p.display_name}</h4>
                      <span className={badgeClass}>{p.risk_level}</span>
                    </div>

                    {/* Risk Probability Gauge */}
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Deficiency Risk Score</span>
                        <strong style={{ color: progressColor, fontSize: '1.1rem' }}>{p.risk_probability}%</strong>
                      </div>
                      <div className="progress-bg">
                        <div className="progress-fill" style={{ width: `${p.risk_probability}%`, background: progressColor }}></div>
                      </div>
                    </div>

                    {/* SHAP Explanation Card */}
                    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#06b6d4', fontWeight: 700, marginBottom: '6px' }}>
                        <Info size={14} /> SHAP Feature Driver Attribution
                      </div>
                      <div style={{ fontSize: '0.88rem', color: 'var(--text-main)', marginBottom: '4px', fontWeight: 600 }}>
                        Key Driving Factor: <span style={{ color: '#38bdf8' }}>{p.top_factor}</span>
                      </div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.45 }}>
                        {p.explanation}
                      </p>
                    </div>
                  </div>

                  {/* Food Recommendations preview */}
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                      Recommended Indian Food Replenishers:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {p.recommended_foods.map((food, fidx) => (
                        <span key={fidx} style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#34d399', fontSize: '0.72rem', padding: '3px 8px', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                          {food}
                        </span>
                      ))}
                    </div>
                  </div>

                </div>
              );
            })}
          </div>

        </div>
      )}

    </div>
  );
}
