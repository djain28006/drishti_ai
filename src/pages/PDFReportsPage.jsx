import React from 'react';
import { FileText, Download, ShieldCheck } from 'lucide-react';

export default function PDFReportsPage({ currentData = {}, apiBase = '' }) {
  const incidents = currentData.incidents || [];

  return (
    <div className="content-area">
      <div>
        <h1 className="page-title">Forensic PDF Reports Center</h1>
        <p className="page-subtitle">Export Official Examination Investigation & Chain of Custody PDFs</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div className="card" style={{ border: '1px solid var(--border-cyan)' }}>
          <div className="card-title" style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }}>
            <FileText size={18} /> Complete Forensic Examination Report
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Comprehensive PDF documenting all detected ROI desk zones, cross-camera incident fusions, motion energy heatmaps, and statistical anomaly scores.
          </p>
          <a 
            href={`${apiBase}/api/report/complete`} 
            target="_blank" 
            rel="noreferrer"
            className="btn-new-investigation"
            style={{ width: 'auto', textDecoration: 'none' }}
          >
            <Download size={14} /> Download Master PDF Report
          </a>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: '12px' }}>
            <ShieldCheck size={18} /> Incident Evidence Capsules
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {incidents.slice(0, 4).map((inc) => (
              <div key={inc.incident_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0a101d', padding: '8px 12px', borderRadius: '4px' }}>
                <span style={{ fontFamily: 'var(--font-mono)', color: '#fff' }}>{inc.incident_id}</span>
                <a 
                  href={`${apiBase}/api/report/capsule/${inc.incident_id}`}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: 'var(--accent-cyan)', fontSize: '11px', fontFamily: 'var(--font-mono)' }}
                >
                  Download PDF →
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
