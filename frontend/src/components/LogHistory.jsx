import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, Utensils, Flame, Zap, Shield, ChevronRight, AlertCircle } from 'lucide-react';

export default function LogHistory({ userProfile }) {
  const [historyData, setHistoryData] = useState([]);
  const [selectedDay, setSelectedDay] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, [userProfile]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const uid = userProfile?.id || 1;
      const res = await axios.get(`/api/logs/history/${uid}`);
      setHistoryData(res.data.history || []);
      if (res.data.history && res.data.history.length > 0) {
        setSelectedDay(res.data.history[0]);
      }
    } catch (err) {
      console.error('Failed to fetch log history:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }} className="animate-fade-in">
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <Calendar size={22} color="#06b6d4" />
              Multi-Day Food Log History
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              View your historical food logs, caloric trends, and micronutrient intake across all past days.
            </p>
          </div>
          <span className="badge-low" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#38bdf8' }}>
            {historyData.length} Days Logged
          </span>
        </div>
      </div>

      {loading ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading log history...
        </div>
      ) : historyData.length === 0 ? (
        <div className="glass-panel" style={{ padding: '50px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <AlertCircle size={36} color="var(--warning-amber)" style={{ marginBottom: '12px' }} />
          <h3>No Historical Logs Available Yet</h3>
          <p style={{ fontSize: '0.9rem', maxWidth: '450px', margin: '8px auto 0 auto' }}>
            Log your meals daily in the Food Logger tab to build your multi-day dietary history timeline.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          
          {/* Days Timeline Sidebar */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>History Timeline</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '420px', overflowY: 'auto' }}>
              {historyData.map((day, idx) => {
                const isSelected = selectedDay && selectedDay.date === day.date;
                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedDay(day)}
                    style={{
                      padding: '14px 16px',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      background: isSelected ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(16, 185, 129, 0.2))' : 'rgba(255,255,255,0.03)',
                      border: isSelected ? '1px solid #06b6d4' : '1px solid rgba(255,255,255,0.06)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem', color: isSelected ? '#38bdf8' : 'var(--text-main)' }}>
                        📅 {day.date}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {day.total_items} items logged
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#34d399' }}>{day.calories_kcal} kcal</div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Iron: {day.iron_mg}mg</div>
                      </div>
                      <ChevronRight size={16} color="var(--text-dim)" />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Selected Day Details Panel */}
          {selectedDay && (
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', pb: '14px' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#06b6d4', fontWeight: 700, textTransform: 'uppercase' }}>Selected Date Summary</span>
                  <h3 style={{ fontSize: '1.3rem', marginTop: '2px' }}>{selectedDay.date}</h3>
                </div>
                <span className="badge-low" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#38bdf8' }}>
                  {selectedDay.total_items} items
                </span>
              </div>

              {/* Day Macro Chips */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Calories</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8' }}>{selectedDay.calories_kcal} kcal</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Protein</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>{selectedDay.protein_g} g</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Iron</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#a7f3d0' }}>{selectedDay.iron_mg} mg</div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '10px', textAlign: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Vitamin C</span>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fde047' }}>{selectedDay.vitamin_c_mg} mg</div>
                </div>
              </div>

              {/* Day Food Breakdown Table */}
              <div>
                <h4 style={{ fontSize: '0.95rem', marginBottom: '10px', color: 'var(--text-muted)' }}>Logged Items for {selectedDay.date}:</h4>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                        <th style={{ padding: '8px' }}>Food Name</th>
                        <th style={{ padding: '8px' }}>Portion</th>
                        <th style={{ padding: '8px' }}>Calories</th>
                        <th style={{ padding: '8px' }}>Iron</th>
                        <th style={{ padding: '8px' }}>Calcium</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedDay.items.map((item, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                          <td style={{ padding: '8px', fontWeight: 600 }}>{item.food_name}</td>
                          <td style={{ padding: '8px' }}>{item.serving_size_g}g</td>
                          <td style={{ padding: '8px', color: '#38bdf8' }}>{item.calories_kcal} kcal</td>
                          <td style={{ padding: '8px', color: '#34d399' }}>{item.iron_mg} mg</td>
                          <td style={{ padding: '8px', color: '#a7f3d0' }}>{item.calcium_mg} mg</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

        </div>
      )}

    </div>
  );
}
