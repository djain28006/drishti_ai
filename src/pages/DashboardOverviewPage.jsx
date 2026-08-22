import React from 'react';
import { Download, ShieldCheck, Zap, AlertTriangle, Layers, Film } from 'lucide-react';

export default function DashboardOverviewPage({ currentData = {}, funnelMetrics = {}, onOpenModal, setCurrentPage, apiBase = '' }) {
  const d = currentData;
  const f = funnelMetrics || {
    raw_motion_triggers: 48,
    noise_filtered_meaningful: d.total_events || 11,
    anomalous_events: (d.events || []).filter(e => e.class_name !== 'student').length || 8,
    fused_incidents: (d.incidents || []).length || 7,
    high_priority: (d.incidents || []).filter(i => i.risk_level === 'HIGH' || i.risk_level === 'CRITICAL').length || 3,
    critical_priority: (d.incidents || []).filter(i => i.risk_level === 'CRITICAL').length || 1,
    processing_time: '8.4s',
    compression_ratio: '85%'
  };

  const incidents = d.incidents || [];
  const topIncidents = incidents.slice(0, 4);

  return (
    <div className="content-area">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Forensic Surveillance Overview</h1>
          <p className="page-subtitle">Offline Video Forensics & Multi-Camera Investigation Dashboard | Session: <strong>{d.video_name || 'Examination_Surveillance.mp4'}</strong></p>
        </div>
        <a 
          className="btn-new-investigation" 
          href={`${apiBase}/api/report/complete`} 
          target="_blank" 
          rel="noreferrer"
          style={{ width: 'auto', textDecoration: 'none' }}
        >
          <Download size={14} /> Export Forensic Report PDF
        </a>
      </div>

      {/* Forensic Reduction Funnel */}
      <div className="card">
        <div className="card-title" style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--accent-cyan)', marginBottom: '14px' }}>
          <Zap size={16} /> Forensic Evidence Reduction Funnel
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
          <div style={{ background: '#0a101d', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Raw Motion ROI</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{f.raw_motion_triggers}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Pixel-level MOG2 bursts</div>
          </div>

          <div style={{ background: '#0a101d', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Noise-Filtered</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{f.noise_filtered_meaningful}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Hysteresis verified</div>
          </div>

          <div style={{ background: '#0a101d', border: '1px solid var(--border-cyan)', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Anomalous Activity</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--status-high)', fontFamily: 'var(--font-mono)' }}>{f.anomalous_events}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Baseline deviation &gt; Z</div>
          </div>

          <div style={{ background: 'rgba(255, 59, 92, 0.1)', border: '1px solid var(--status-critical)', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Fused Incidents</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--status-critical)', fontFamily: 'var(--font-mono)' }}>{f.fused_incidents}</div>
            <div style={{ fontSize: '10px', color: 'var(--status-critical)' }}>{f.high_priority} Priority ({f.critical_priority} Critical)</div>
          </div>
        </div>
      </div>

      {/* Overview Cards & Telemetry Feed */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">Active Telemetry Signals</div>
            <button className="sidebar-footer-item" onClick={() => setCurrentPage('artifacts')}>View Analytics →</button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {topIncidents.map((inc) => (
              <div 
                key={inc.incident_id} 
                style={{
                  background: '#0a101d',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  padding: '12px 16px',
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer'
                }}
                onClick={() => onOpenModal && onOpenModal(inc.incident_id)}
              >
                <div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                    <span className={`badge ${inc.risk_level === 'CRITICAL' ? 'badge-critical' : inc.risk_level === 'HIGH' ? 'badge-high' : 'badge-med'}`}>{inc.risk_level}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: '#fff' }}>{inc.incident_id}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    📍 {inc.location_desc || 'Desk Area'} | ⏱️ {inc.duration_seconds ? inc.duration_seconds.toFixed(1) : '8.5'}s
                  </div>
                </div>

                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', fontSize: '14px', color: 'var(--accent-cyan)' }}>
                  Risk: {inc.risk_score}/100
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="card-title" style={{ marginBottom: '12px' }}>System Metrics</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Detected Desks:</span>
                <span style={{ color: 'var(--accent-cyan)' }}>{d.detected_zones || 12}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Compression Ratio:</span>
                <span style={{ color: 'var(--accent-cyan)' }}>{f.compression_ratio}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Pipeline Execution:</span>
                <span style={{ color: 'var(--status-nominal)' }}>{f.processing_time}</span>
              </div>
            </div>
          </div>

          <button 
            className="btn-new-investigation"
            style={{ marginTop: '20px' }}
            onClick={() => setCurrentPage('upload')}
          >
            Ingest New CCTV Video
          </button>
        </div>
      </div>
    </div>
  );
}
