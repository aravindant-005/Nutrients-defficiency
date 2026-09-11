import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Database, Server, CheckCircle, FileText, RefreshCw, Terminal } from 'lucide-react';

export default function DatabaseSettings() {
  const [dbStatus, setDbStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDbStatus();
  }, []);

  const fetchDbStatus = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/db/status');
      setDbStatus(res.data);
    } catch (err) {
      console.error('Failed to fetch DB status:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      
      {/* Header */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <Database size={22} color="#10b981" />
          PostgreSQL & pgAdmin Database Status
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Configured for PostgreSQL persistence with auto-fallback to embedded SQLite for instant execution.
        </p>
      </div>

      {loading ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Checking database status...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Connection Status Card */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Server size={20} color="#34d399" />
                <h3 style={{ fontSize: '1.1rem' }}>Active Database Engine</h3>
              </div>
              <span className="badge-low" style={{ textTransform: 'uppercase', fontSize: '0.85rem' }}>
                {dbStatus?.database_engine}
              </span>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.9)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)', fontFamily: 'monospace', fontSize: '0.85rem', color: '#38bdf8', marginBottom: '16px' }}>
              Connection: {dbStatus?.postgres_connection_string}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Engine Type</span>
                <strong style={{ fontSize: '0.95rem', color: '#10b981' }}>{dbStatus?.database_engine.toUpperCase()}</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Operational Health</span>
                <strong style={{ fontSize: '0.95rem', color: '#34d399' }}>{dbStatus?.status}</strong>
              </div>
            </div>
          </div>

          {/* PostgreSQL pgAdmin Setup Instructions */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Terminal size={18} color="#06b6d4" />
              pgAdmin Setup & PostgreSQL Schema Import
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
              To connect this project directly to your local **pgAdmin / PostgreSQL** installation:
            </p>

            <ol style={{ paddingLeft: '20px', fontSize: '0.85rem', color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '10px', lineHeight: 1.5 }}>
              <li>Open **pgAdmin 4** on your local machine and connect to PostgreSQL.</li>
              <li>Create a new database named <code>micronutrient_db</code>.</li>
              <li>Open Query Tool in pgAdmin and execute the included <code>backend/schema.sql</code> DDL script to generate the <code>user_profiles</code>, <code>food_log_items</code>, and <code>prediction_results</code> tables.</li>
              <li>Set your environment variable or update <code>backend/database.py</code> connection parameters if your password differs from <code>postgres:postgres</code>.</li>
            </ol>
          </div>

        </div>
      )}

    </div>
  );
}
