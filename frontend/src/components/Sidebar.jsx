import React from 'react';
import { Activity, Utensils, AlertTriangle, Lightbulb, Calendar, User, LogOut, ShieldCheck, ChevronRight } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, userProfile, onLogout }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard Overview', icon: Activity },
    { id: 'logger', label: 'Smart Food Logger', icon: Utensils },
    { id: 'risk', label: 'AI Risk & SHAP Analysis', icon: AlertTriangle },
    { id: 'recommendations', label: 'Diet Recommendations', icon: Lightbulb },
    { id: 'history', label: 'Multi-Day History', icon: Calendar },
    { id: 'profile', label: 'Profile & Health Tags', icon: User },
  ];

  return (
    <aside
      style={{
        width: '270px',
        minWidth: '270px',
        background: 'var(--bg-sidebar)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        borderRight: '1px solid var(--border-card)',
        display: 'flex',
        flexDirection: 'column',
        justify: 'space-between',
        padding: '24px 16px',
        height: '100vh',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}
    >
      {/* Top Header & Brand */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px 24px 8px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ background: 'linear-gradient(135deg, #06b6d4, #10b981)', padding: '10px', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 16px rgba(6, 182, 212, 0.4)' }}>
            <ShieldCheck size={24} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }} className="gradient-text">
              NutriDetect AI
            </h1>
            <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', margin: 0, fontWeight: 500 }}>
              Micronutrient Intelligence
            </p>
          </div>
        </div>

        {/* Navigation List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '20px' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0 10px 6px 10px' }}>
            Main Navigation
          </span>
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
                  justify: 'space-between',
                  padding: '12px 14px',
                  borderRadius: '12px',
                  fontSize: '0.88rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  background: isActive ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.22), rgba(16, 185, 129, 0.22))' : 'transparent',
                  color: isActive ? '#38bdf8' : 'var(--text-muted)',
                  boxShadow: isActive ? '0 0 0 1px rgba(6, 182, 212, 0.4)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Icon size={18} color={isActive ? '#38bdf8' : 'var(--text-muted)'} />
                  <span>{item.label}</span>
                </div>
                {isActive && <ChevronRight size={16} color="#38bdf8" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom User Profile Capsule & Logout */}
      {userProfile && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.03)', padding: '10px 12px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, #06b6d4, #3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.9rem', color: '#ffffff' }}>
              {userProfile.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div style={{ overflow: 'hidden', flex: 1 }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {userProfile.name}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#34d399', fontWeight: 600 }}>
                {userProfile.diet_type || 'Vegetarian'}
              </div>
            </div>
          </div>

          <button
            onClick={onLogout}
            className="btn-danger"
            style={{ width: '100%', justifyContent: 'center', padding: '10px', fontSize: '0.85rem', borderRadius: '10px' }}
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      )}

    </aside>
  );
}
