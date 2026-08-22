import React, { useState } from 'react';
import { Filter, Download, ShieldAlert, Eye } from 'lucide-react';

export default function PriorityIncidentsPage({ currentData = {}, onOpenModal }) {
  const [filterRisk, setFilterRisk] = useState('ALL');
  const incidents = currentData.incidents || [];

  const filteredIncidents = incidents.filter(inc => {
    if (filterRisk === 'ALL') return true;
    return inc.risk_level === filterRisk;
  });

  return (
    <div className="content-area">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Priority Incident Queue</h1>
          <p className="page-subtitle">Ranked & Fused Cross-Camera Behavioral Anomalies</p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(level => (
            <button
              key={level}
              onClick={() => setFilterRisk(level)}
              style={{
                background: filterRisk === level ? 'var(--accent-cyan)' : 'var(--bg-darkest)',
                color: filterRisk === level ? '#070d17' : 'var(--text-muted)',
                border: '1px solid var(--border-color)',
                borderRadius: '4px',
                padding: '6px 12px',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredIncidents.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No incidents found matching filter "{filterRisk}"
          </div>
        ) : (
          filteredIncidents.map(inc => (
            <div 
              key={inc.incident_id} 
              className="card"
              style={{
                display: 'flex',
                justify: 'space-between',
                alignItems: 'center',
                borderLeft: `4px solid ${inc.risk_level === 'CRITICAL' ? 'var(--status-critical)' : inc.risk_level === 'HIGH' ? 'var(--status-high)' : 'var(--status-medium)'}`
              }}
            >
              <div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                  <span className={`badge ${inc.risk_level === 'CRITICAL' ? 'badge-critical' : inc.risk_level === 'HIGH' ? 'badge-high' : 'badge-med'}`}>{inc.risk_level}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', fontWeight: '800', color: '#fff' }}>{inc.incident_id}</span>
                  <span className="badge" style={{ background: 'rgba(0, 242, 255, 0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--border-cyan)' }}>
                    {(inc.primary_class || inc.primary_behavior || 'BEHAVIOR').toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  📍 {inc.location_desc || `Desk S${inc.zone_id || '1'}`} | Duration: {(inc.duration_seconds || 8.5).toFixed(1)}s
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', fontSize: '16px', color: 'var(--accent-cyan)' }}>
                  Risk: {inc.risk_score}/100
                </div>

                <button 
                  className="btn-new-investigation"
                  style={{ width: 'auto' }}
                  onClick={() => onOpenModal && onOpenModal(inc.incident_id)}
                >
                  <Eye size={14} /> Inspect Capsule
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
