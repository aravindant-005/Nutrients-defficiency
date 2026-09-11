import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Lightbulb, Utensils, CheckCircle, ShieldCheck, AlertCircle, PlusCircle } from 'lucide-react';

export default function Recommendations({ userProfile, onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecommendations();
  }, [userProfile]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const uid = userProfile?.id || 1;
      const res = await axios.get(`/api/recommendations/${uid}`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const hasLogged = data ? data.has_logged_data : true;
  const recommendations = data ? data.recommendations : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }} className="animate-fade-in">
      
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(59, 130, 246, 0.15))', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <Lightbulb size={22} color="#06b6d4" />
              AI Indian Food Recommendation Engine
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Personalized dietary replenishers mapped directly from the <strong>INDB (Indian Nutrient Databank)</strong> dataset.
            </p>
          </div>
          {userProfile && (
            <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '6px 14px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ShieldCheck size={16} />
              Filtered for: {userProfile.diet_type || 'Vegetarian'}
            </div>
          )}
        </div>
      </div>

      {/* Dietary Synergy Tips */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '18px', borderColor: 'rgba(52, 211, 153, 0.3)' }}>
          <div style={{ fontWeight: 700, color: '#34d399', fontSize: '0.9rem', marginBottom: '4px' }}>💡 Synergy Tip #1: Iron + Vitamin C</div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
            Squeezing lemon juice (Vit C) over Spinach/Lentils increases non-heme iron absorption by up to 300%.
          </p>
        </div>
        <div className="glass-panel" style={{ padding: '18px', borderColor: 'rgba(56, 189, 248, 0.3)' }}>
          <div style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.9rem', marginBottom: '4px' }}>💡 Synergy Tip #2: Calcium + Vitamin D</div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
            Vitamin D is essential for active intestinal calcium transport. Consume fortified dairy/milk with sunlight exposure.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading AI recommendations...</div>
      ) : !hasLogged ? (
        <div className="glass-panel" style={{ padding: '50px', textAlign: 'center', borderColor: 'rgba(245, 158, 11, 0.4)' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
            <AlertCircle size={36} color="var(--warning-amber)" />
          </div>
          <h3 style={{ fontSize: '1.3rem', marginBottom: '8px' }}>Log Your Meals First!</h3>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto 20px auto', lineHeight: 1.5 }}>
            To view AI-suggested Indian food replenishers tailored to your deficiencies, log your daily meals in the Food Logger tab.
          </p>
          <button className="btn-primary" onClick={() => onNavigate('logger')}>
            <PlusCircle size={18} />
            Go to Food Logger
          </button>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
          <CheckCircle size={36} color="#34d399" style={{ marginBottom: '10px' }} />
          <h3>Optimal Micronutrient Balance</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Your current food log meets your target dietary thresholds!</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {recommendations.map((rec, idx) => (
            <div key={idx} className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#06b6d4', textTransform: 'uppercase' }}>Target Deficient Nutrient</span>
                  <h3 style={{ fontSize: '1.25rem' }}>{rec.display_name} Replenishers</h3>
                </div>
                <span className={rec.risk_level === 'High Risk' ? 'badge-high' : 'badge-moderate'}>
                  {rec.risk_level} ({rec.risk_probability}%)
                </span>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                <strong>SHAP Model Insight:</strong> {rec.shap_explanation}
              </p>

              <h4 style={{ fontSize: '0.95rem', marginBottom: '10px', color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Utensils size={16} /> Recommended {rec.diet_type} Indian Foods (High in {rec.display_name}):
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                {rec.recommended_indian_foods.map((food, fidx) => (
                  <div key={fidx} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '12px 14px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399' }}></div>
                    <span style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-main)' }}>{food}</span>
                  </div>
                ))}
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  );
}
