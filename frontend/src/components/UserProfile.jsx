import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { User, Save, CheckCircle, Heart, Scale, Activity, ShieldCheck } from 'lucide-react';

export default function UserProfile({ userProfile, onProfileUpdate }) {
  const [formData, setFormData] = useState({
    name: '',
    age: 28,
    gender: 1.0,
    weight_kg: 70,
    height_cm: 175,
    activity_level: 'Moderate',
    diet_type: 'Vegetarian',
    health_conditions: 'Anemia, Vitamin D Deficiency',
    daily_calorie_goal: 2000
  });

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const medicalConditionList = [
    "Anemia", "Vitamin D Deficiency", "Diabetes", "Lactose Intolerance", "Thyroid", "Osteoporosis", "Hypertension"
  ];

  useEffect(() => {
    if (userProfile) {
      setFormData({
        name: userProfile.name || '',
        age: userProfile.age || 28,
        gender: userProfile.gender !== undefined ? userProfile.gender : 1.0,
        weight_kg: userProfile.weight_kg || 70,
        height_cm: userProfile.height_cm || 175,
        activity_level: userProfile.activity_level || 'Moderate',
        diet_type: userProfile.diet_type || 'Vegetarian',
        health_conditions: userProfile.health_conditions || 'Anemia, Vitamin D Deficiency',
        daily_calorie_goal: userProfile.daily_calorie_goal || 2000
      });
    }
  }, [userProfile]);

  const activeConditions = formData.health_conditions
    ? formData.health_conditions.split(',').map(s => s.trim()).filter(Boolean)
    : [];

  const handleConditionToggle = (condition) => {
    let updated;
    if (activeConditions.includes(condition)) {
      updated = activeConditions.filter(c => c !== condition);
    } else {
      updated = [...activeConditions, condition];
    }
    setFormData(prev => ({
      ...prev,
      health_conditions: updated.join(', ')
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg('');

    try {
      const uid = userProfile?.id || 1;
      const res = await axios.post(`/api/profile/update/${uid}`, {
        name: formData.name,
        age: parseFloat(formData.age),
        gender: parseFloat(formData.gender),
        weight_kg: parseFloat(formData.weight_kg),
        height_cm: parseFloat(formData.height_cm),
        activity_level: formData.activity_level,
        diet_type: formData.diet_type,
        health_conditions: formData.health_conditions,
        daily_calorie_goal: parseFloat(formData.daily_calorie_goal)
      });

      setSuccessMsg('Profile and medical settings saved successfully!');
      setTimeout(() => setSuccessMsg(''), 3500);

      if (onProfileUpdate) {
        onProfileUpdate();
      }
    } catch (err) {
      console.error('Failed to update profile:', err);
    } finally {
      setSaving(false);
    }
  };

  const bmi = (formData.weight_kg / ((formData.height_cm / 100.0) ** 2)).toFixed(2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }} className="animate-fade-in">
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <User size={22} color="#06b6d4" />
              User Health Profile & Medical Tag Settings
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Manage your biometric parameters, dietary restrictions, and medical condition tags for ML predictions.
            </p>
          </div>
          <span className="badge-low" style={{ background: 'rgba(6, 182, 212, 0.15)', color: '#38bdf8' }}>
            BMI: {bmi} kg/m²
          </span>
        </div>
      </div>

      {successMsg && (
        <div className="glass-panel" style={{ padding: '14px 20px', background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10b981', color: '#34d399', display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 600 }}>
          <CheckCircle size={20} />
          {successMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Biometrics & Demographics */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <h3 style={{ fontSize: '1.15rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Scale size={18} /> Biometric & Personal Details
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
                Full Name
              </label>
              <input
                type="text"
                className="input-control"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
                Age (Years)
              </label>
              <input
                type="number"
                className="input-control"
                value={formData.age}
                onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
                Biological Sex
              </label>
              <select
                className="input-control"
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: parseFloat(e.target.value) })}
              >
                <option value={1.0}>Male</option>
                <option value={2.0}>Female</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
                Weight (kg)
              </label>
              <input
                type="number"
                step="0.5"
                className="input-control"
                value={formData.weight_kg}
                onChange={(e) => setFormData({ ...formData, weight_kg: e.target.value })}
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
                Height (cm)
              </label>
              <input
                type="number"
                step="0.5"
                className="input-control"
                value={formData.height_cm}
                onChange={(e) => setFormData({ ...formData, height_cm: e.target.value })}
                required
              />
            </div>

            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px', fontWeight: 600 }}>
                Daily Calorie Target (kcal)
              </label>
              <input
                type="number"
                className="input-control"
                value={formData.daily_calorie_goal}
                onChange={(e) => setFormData({ ...formData, daily_calorie_goal: e.target.value })}
                required
              />
            </div>
          </div>
        </div>

        {/* Dietary Preferences & Medical Conditions */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '1.15rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Heart size={18} /> Dietary Preferences & Medical Condition Tags
          </h3>

          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
              Primary Dietary Classification (Used for Recommendation Filtering)
            </label>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {['Vegetarian', 'Vegan', 'Non-Vegetarian'].map((type) => (
                <button
                  type="button"
                  key={type}
                  className="btn-secondary"
                  style={{
                    background: formData.diet_type === type ? 'rgba(16, 185, 129, 0.25)' : undefined,
                    borderColor: formData.diet_type === type ? '#10b981' : undefined,
                    color: formData.diet_type === type ? '#34d399' : undefined
                  }}
                  onClick={() => setFormData({ ...formData, diet_type: type })}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Medical Tags */}
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
              Known Medical Conditions / Diagnostic Flags (Click to Toggle):
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {medicalConditionList.map((cond, idx) => {
                const isActive = activeConditions.includes(cond);
                return (
                  <button
                    type="button"
                    key={idx}
                    onClick={() => handleConditionToggle(cond)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '9999px',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      background: isActive ? 'rgba(244, 63, 94, 0.25)' : 'rgba(255,255,255,0.04)',
                      color: isActive ? '#f87171' : 'var(--text-muted)',
                      border: isActive ? '1px solid #f43f5e' : '1px solid rgba(255,255,255,0.08)'
                    }}
                  >
                    {isActive ? '✓ ' : '+ '} {cond}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="btn-primary"
          style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '1rem' }}
          disabled={saving}
        >
          <Save size={18} />
          {saving ? 'Saving Profile...' : 'Save Profile & Update Settings'}
        </button>

      </form>

    </div>
  );
}
