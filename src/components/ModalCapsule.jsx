import React from 'react';
import { X, Download, ShieldAlert, Clock, MapPin, Film } from 'lucide-react';

export default function ModalCapsule({ incident, onClose, apiBase = '' }) {
  if (!incident) return null;

  const riskLevel = incident.risk_level || 'HIGH';
  const riskScore = incident.risk_score || 80;
  const incidentId = incident.incident_id || 'INC-FB313E';
  const primaryBehavior = (incident.primary_class || incident.primary_behavior || 'ANOMALY DETECTED').toUpperCase();

  let clipKey = incidentId;
  if (incident.clip_path) {
    const match = incident.clip_path.match(/event_([^\\\/]+)\.mp4/i);
    if (match) clipKey = match[1];
    else clipKey = incident.clip_path.split(/[\\\/]/).pop().replace(/\.mp4$/i, "");
  } else if (incident.related_event_ids && incident.related_event_ids.length > 0) {
    clipKey = incident.related_event_ids[0];
  }
  const clipUrl = `${apiBase}/api/media/clip/${encodeURIComponent(clipKey)}`;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          <X size={20} />
        </button>

        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
            <span className={`badge ${riskLevel === 'CRITICAL' ? 'badge-critical' : riskLevel === 'HIGH' ? 'badge-high' : 'badge-med'}`}>
              <ShieldAlert size={12} /> {riskLevel} RISK ({riskScore}/100)
            </span>
            <span className="badge" style={{ background: 'rgba(0, 242, 255, 0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--border-cyan)' }}>
              {primaryBehavior}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              CAPSULE ID: <strong>CAP-{incidentId}</strong>
            </span>
          </div>

          <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#fff', margin: '4px 0' }}>
            Forensic Evidence Capsule: {incidentId}
          </h2>

          <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            <span><MapPin size={12} style={{ verticalAlign: 'middle' }} /> Location: <strong style={{ color: '#fff' }}>{incident.location_desc || `Desk S${incident.zone_id || '4'}`}</strong></span>
            <span><Clock size={12} style={{ verticalAlign: 'middle' }} /> Duration: <strong style={{ color: '#fff' }}>{(incident.duration_seconds || 8.75).toFixed(2)}s</strong></span>
          </div>
        </div>

        {/* Video Player */}
        <div style={{ position: 'relative', borderRadius: '8px', overflow: 'hidden', background: '#000', marginBottom: '16px', border: '1px solid var(--border-color)' }}>
          <video 
            src={clipUrl} 
            controls 
            autoPlay 
            loop 
            muted 
            style={{ width: '100%', maxHeight: '380px', display: 'block' }}
          >
            <source src={clipUrl} type="video/mp4" />
          </video>
        </div>

        {/* Math Factor Attribution */}
        <div style={{ marginBottom: '16px', padding: '12px', background: 'var(--bg-darkest)', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)', marginBottom: '6px' }}>
            MATH FACTOR ATTRIBUTION
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span style={{ background: 'rgba(0, 242, 255, 0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--border-cyan)', padding: '3px 10px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: '700' }}>
              +25 Motion
            </span>
            <span style={{ background: 'rgba(255, 138, 0, 0.15)', color: 'var(--status-high)', border: '1px solid rgba(255, 138, 0, 0.4)', padding: '3px 10px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: '700' }}>
              +18 Gaze
            </span>
            <span style={{ background: 'rgba(255, 59, 92, 0.15)', color: 'var(--status-critical)', border: '1px solid rgba(255, 59, 92, 0.4)', padding: '3px 10px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '11px', fontWeight: '700' }}>
              +45 Object ID
            </span>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
          <button 
            className="btn-new-investigation" 
            style={{ width: 'auto', background: 'transparent', color: 'var(--text-main)', border: '1px solid var(--border-color)', boxShadow: 'none' }}
            onClick={onClose}
          >
            Close
          </button>
          <a 
            href={`${apiBase}/api/report/capsule/${encodeURIComponent(incidentId)}`} 
            target="_blank" 
            rel="noreferrer"
            className="btn-new-investigation"
            style={{ width: 'auto', textDecoration: 'none' }}
          >
            <Download size={14} /> Export Capsule PDF
          </a>
        </div>
      </div>
    </div>
  );
}
