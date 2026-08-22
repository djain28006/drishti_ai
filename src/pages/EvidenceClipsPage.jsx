import React from 'react';
import { Film, Play, Eye } from 'lucide-react';

export default function EvidenceClipsPage({ currentData = {}, onOpenModal }) {
  const incidents = currentData.incidents || [];

  return (
    <div className="content-area">
      <div>
        <h1 className="page-title">Evidence Clips Gallery</h1>
        <p className="page-subtitle">Extracted ROI Video Clips & Behavioral Anomaly Segments</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {incidents.map((inc) => (
          <div key={inc.incident_id} className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <div style={{ height: '160px', background: '#050912', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
              <Film size={36} style={{ color: 'var(--accent-cyan)', opacity: 0.5 }} />
              <button 
                className="btn-new-investigation"
                style={{ position: 'absolute', width: 'auto', padding: '8px 16px' }}
                onClick={() => onOpenModal && onOpenModal(inc.incident_id)}
              >
                <Play size={14} /> Play Clip
              </button>
            </div>

            <div style={{ padding: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: '#fff' }}>{inc.incident_id}</span>
                <span className={`badge ${inc.risk_level === 'CRITICAL' ? 'badge-critical' : 'badge-high'}`}>{inc.risk_level}</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                📍 {inc.location_desc || 'Desk Location'} | {(inc.duration_seconds || 8.5).toFixed(1)}s
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
