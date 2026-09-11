import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Plus, Trash2, Utensils, Check, Scale, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function FoodLogger({ userProfile, dailyData, refreshData }) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedFood, setSelectedFood] = useState(null);
  const [servingSize, setServingSize] = useState(100);
  const [loading, setLoading] = useState(false);
  const [addedSuccessMsg, setAddedSuccessMsg] = useState(null);

  const quickPills = [
    "Palak Paneer", "Roti", "Dal Fry", "Amla", "Rajma", "Curd", "Egg Curry", "Paneer Tikka", "Biryani"
  ];

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchSearch(query.trim());
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const fetchSearch = async (searchTerm) => {
    setLoading(true);
    try {
      const res = await axios.get(`/api/food/search?q=${encodeURIComponent(searchTerm)}&limit=15`);
      setSearchResults(res.data);
      if (res.data.length > 0 && !selectedFood) {
        setSelectedFood(res.data[0]);
      }
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLog = async () => {
    if (!selectedFood) return;
    const currentUserId = userProfile?.id || 1;

    try {
      await axios.post('/api/logs/add', {
        user_id: currentUserId,
        food_code: selectedFood.food_code,
        food_name: selectedFood.food_name,
        serving_size_g: parseFloat(servingSize),
        calories_kcal: selectedFood.calories_kcal,
        protein_g: selectedFood.protein_g,
        carbs_g: selectedFood.carbs_g,
        fat_g: selectedFood.fat_g,
        fiber_g: selectedFood.fiber_g,
        iron_mg: selectedFood.iron_mg,
        calcium_mg: selectedFood.calcium_mg,
        vitamin_d_mcg: selectedFood.vitamin_d_mcg,
        vitamin_b12_mcg: selectedFood.vitamin_b12_mcg,
        zinc_mg: selectedFood.zinc_mg,
        magnesium_mg: selectedFood.magnesium_mg,
        vitamin_c_mg: selectedFood.vitamin_c_mg
      });

      setAddedSuccessMsg(`Successfully logged ${selectedFood.food_name} (${servingSize}g) to your account!`);
      setTimeout(() => setAddedSuccessMsg(null), 3500);
      refreshData();
    } catch (err) {
      console.error('Failed to log food:', err);
    }
  };

  const handleDeleteItem = async (id) => {
    try {
      await axios.delete(`/api/logs/delete/${id}`);
      refreshData();
    } catch (err) {
      console.error('Failed to delete log item:', err);
    }
  };

  const ratio = servingSize / 100.0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }} className="animate-fade-in">
      
      {/* Success Alert Banner */}
      {addedSuccessMsg && (
        <div className="glass-panel" style={{ padding: '14px 20px', background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10b981', color: '#34d399', display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 600 }}>
          <CheckCircle2 size={20} />
          {addedSuccessMsg}
        </div>
      )}

      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <Utensils size={22} color="#10b981" />
              Real-Time Indian Food Logger (INDB Databank)
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Search from <strong>1,000+ Indian dishes & whole foods</strong> to compute precise daily macro and micronutrients.
            </p>
          </div>
          <span className="badge-low" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}>
            {dailyData?.logs?.length || 0} Meals Logged Today
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
        
        {/* Search Panel */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Search Foods & Dishes</h3>

          {/* Quick Search Pills */}
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
              Popular Indian Food Search Chips:
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {quickPills.map((pill, idx) => (
                <button
                  key={idx}
                  className="food-pill"
                  onClick={() => setQuery(pill)}
                >
                  {pill}
                </button>
              ))}
            </div>
          </div>

          {/* Search Bar */}
          <div style={{ position: 'relative' }}>
            <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              className="input-control"
              style={{ paddingLeft: '42px' }}
              placeholder="Type food name (e.g. Palak Paneer, Roti, Dal Fry, Amla)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          {/* Results List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '280px', overflowY: 'auto' }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>Searching Databank...</div>
            ) : searchResults.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>No foods found matching "{query}"</div>
            ) : (
              searchResults.map((item, idx) => {
                const isSelected = selectedFood && selectedFood.food_name === item.food_name;
                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedFood(item)}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(16, 185, 129, 0.18)' : 'rgba(255,255,255,0.03)',
                      border: isSelected ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.06)',
                      display: 'flex',
                      justify: 'space-between',
                      alignItems: 'center',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: isSelected ? '#34d399' : 'var(--text-main)' }}>{item.food_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.serving_unit}</div>
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>{item.calories_kcal} kcal</span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Selected Food Calculator */}
        {selectedFood && (
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 700, textTransform: 'uppercase' }}>Selected Item</span>
                  <h3 style={{ fontSize: '1.3rem', color: 'var(--text-main)' }}>{selectedFood.food_name}</h3>
                </div>
                <span className="badge-low" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#38bdf8' }}>INDB Verified</span>
              </div>

              {/* Portion Selector Buttons */}
              <div style={{ marginBottom: '20px', background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '12px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '10px', fontWeight: 600 }}>
                  <Scale size={16} /> Portion Size (Grams)
                </label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {[50, 100, 150, 200, 250].map((size) => (
                    <button
                      key={size}
                      className="btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '0.82rem', background: servingSize === size ? 'rgba(16, 185, 129, 0.25)' : undefined, borderColor: servingSize === size ? '#10b981' : undefined }}
                      onClick={() => setServingSize(size)}
                    >
                      {size}g
                    </button>
                  ))}
                </div>
                <input
                  type="number"
                  className="input-control"
                  style={{ marginTop: '10px' }}
                  value={servingSize}
                  onChange={(e) => setServingSize(Math.max(1, parseFloat(e.target.value) || 0))}
                />
              </div>

              {/* Calculated Nutrients Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', fontSize: '0.85rem' }}>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Energy:</span> <strong>{(selectedFood.calories_kcal * ratio).toFixed(1)} kcal</strong>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Protein:</span> <strong>{(selectedFood.protein_g * ratio).toFixed(1)} g</strong>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Iron:</span> <strong style={{ color: '#34d399' }}>{(selectedFood.iron_mg * ratio).toFixed(2)} mg</strong>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Calcium:</span> <strong style={{ color: '#38bdf8' }}>{(selectedFood.calcium_mg * ratio).toFixed(1)} mg</strong>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Vitamin C:</span> <strong style={{ color: '#fbbf24' }}>{(selectedFood.vitamin_c_mg * ratio).toFixed(1)} mg</strong>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Zinc:</span> <strong style={{ color: '#818cf8' }}>{(selectedFood.zinc_mg * ratio).toFixed(2)} mg</strong>
                </div>
              </div>
            </div>

            <button
              className="btn-primary"
              style={{ width: '100%', marginTop: '20px', justifyContent: 'center', padding: '12px' }}
              onClick={handleAddLog}
            >
              <Plus size={18} />
              Add Item to Today's Food Log
            </button>
          </div>
        )}

      </div>

      {/* Logged Items Table */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '16px' }}>Current Active Food Logs ({dailyData?.logs?.length || 0})</h3>
        
        {dailyData?.logs?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
            <AlertCircle size={28} color="var(--warning-amber)" style={{ marginBottom: '8px' }} />
            <p>No items logged yet today. Use the search tool above to add foods!</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px' }}>Food Item</th>
                  <th style={{ padding: '10px' }}>Portion</th>
                  <th style={{ padding: '10px' }}>Calories</th>
                  <th style={{ padding: '10px' }}>Protein</th>
                  <th style={{ padding: '10px' }}>Iron</th>
                  <th style={{ padding: '10px' }}>Calcium</th>
                  <th style={{ padding: '10px' }}>Vit C</th>
                  <th style={{ padding: '10px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {dailyData.logs.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '10px', fontWeight: 600 }}>{item.food_name}</td>
                    <td style={{ padding: '10px' }}>{item.serving_size_g}g</td>
                    <td style={{ padding: '10px', color: '#38bdf8', fontWeight: 600 }}>{item.calories_kcal} kcal</td>
                    <td style={{ padding: '10px' }}>{item.protein_g} g</td>
                    <td style={{ padding: '10px', color: '#34d399' }}>{item.iron_mg} mg</td>
                    <td style={{ padding: '10px', color: '#a7f3d0' }}>{item.calcium_mg} mg</td>
                    <td style={{ padding: '10px', color: '#fde047' }}>{item.vitamin_c_mg} mg</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      <button className="btn-danger" onClick={() => handleDeleteItem(item.id)}>
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
