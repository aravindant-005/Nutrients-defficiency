import React from 'react';
import { Activity, Utensils, AlertTriangle, Lightbulb, Calendar, User, LogOut, ShieldCheck } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, userProfile, onLogout }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'logger', label: 'Food Logger', icon: Utensils },
    { id: 'risk', label: 'Deficiency Risk & SHAP', icon: AlertTriangle },
    { id: 'recommendations', label: 'AI Recommendations', icon: Lightbulb },
    { id: 'history', label: 'Log History', icon: Calendar },
    { id: 'profile', label: 'Profile & Settings', icon: User },
  ];

  return (
    <nav className="glass-panel" style={{ borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, padding: '14px 28px', position: 'sticky', top: 0, zIndex: 100 }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* Modern Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)' }}>
            <ShieldCheck size={26} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, letterSpacing: '-0.03em' }} className="gradient-text">
              NutriDetect AI
            </h1>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, fontWeight: 500 }}>
              Micronutrient Deficiency System
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflowX: 'auto', padding: '4px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 16px',
                  borderRadius: '10px',
                  fontSize: '0.88rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  background: isActive ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(6, 182, 212, 0.25))' : 'transparent',
                  color: isActive ? '#34d399' : 'var(--text-muted)',
                  boxShadow: isActive ? '0 0 0 1px rgba(52, 211, 153, 0.4)' : 'none'
                }}
              >
                <Icon size={17} />
                {item.label}
              </button>
            );
          })}
        </div>

        {/* User Capsule & Logout Button */}
        {userProfile && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.04)', padding: '6px 14px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, #06b6d4, #3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem' }}>
                {userProfile.name ? userProfile.name.charAt(0) : 'U'}
              </div>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>{userProfile.name}</div>
                <div style={{ fontSize: '0.72rem', color: '#34d399', fontWeight: 600 }}>{userProfile.diet_type || 'Vegetarian'}</div>
              </div>
            </div>

            <button
              onClick={onLogout}
              className="btn-danger"
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px', fontSize: '0.82rem', borderRadius: '10px' }}
              title="Sign Out"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        )}

      </div>
    </nav>
  );
}
