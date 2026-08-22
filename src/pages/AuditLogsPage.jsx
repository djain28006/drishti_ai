import React, { useState } from 'react';
import { Lock, CheckCircle, Filter, Download, ChevronLeft, ChevronRight } from 'lucide-react';

export default function AuditLogsPage() {
  const [operatorFilter, setOperatorFilter] = useState('All');
  const [severityFilter, setSeverityFilter] = useState('All');

  const logs = [
    {
      timestamp: '2023-10-27T14:32:01.005Z',
      operatorId: 'Analyst Alpha-7',
      severity: 'High',
      actionLogged: 'Modify Threshold: Biometric Match Confidence < 95%',
      checksum: '7f83b165...e9a4'
    },
    {
      timestamp: '2023-10-27T14:15:22.198Z',
      operatorId: 'System Auth',
      severity: 'Nominal',
      actionLogged: 'Automated Key Rotation (Vault Node 3)',
      checksum: '3a22c981...11b0'
    },
    {
      timestamp: '2023-10-27T13:45:09.771Z',
      operatorId: 'Analyst Alpha-7',
      severity: 'Medium',
      actionLogged: 'Export Dossier: Subject #4489 (Encrypted Package)',
      checksum: 'b9c410dd...f322'
    },
    {
      timestamp: '2023-10-27T12:10:00.000Z',
      operatorId: 'Forensics Bot',
      severity: 'Nominal',
      actionLogged: 'Ingest Artifact: CCTV_Feed_Sector4_Raw.mp4',
      checksum: 'd41d8cd9...8f00'
    },
    {
      timestamp: '2023-10-27T09:05:12.443Z',
      operatorId: 'Analyst Beta-2',
      severity: 'High',
      actionLogged: 'Override Access Request: Spatial Grid Alpha (Granted)',
      checksum: '88a53e4c...77a1'
    }
  ];

  const handleExportCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," 
      + ["Timestamp (UTC),Operator ID,Severity,Action Logged,SHA-256 Checksum"]
      .concat(logs.map(l => `"${l.timestamp}","${l.operatorId}","${l.severity}","${l.actionLogged}","${l.checksum}"`))
      .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "drishti_audit_logs.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="content-area">
      {/* Header & Vault Status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Chain of Custody & Audit Log</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '6px', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--text-muted)' }}>Vault Security Status:</span>
            <span className="badge" style={{ background: 'rgba(0, 242, 255, 0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--border-cyan)' }}>
              <Lock size={12} /> LOCKED <CheckCircle size={12} />
            </span>
          </div>
        </div>

        {/* Filter & Export Controls */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select 
            value={operatorFilter} 
            onChange={(e) => setOperatorFilter(e.target.value)}
            style={{ background: '#0a101d', border: '1px solid var(--border-color)', color: 'var(--text-main)', padding: '6px 12px', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
          >
            <option value="All">All Operators</option>
            <option value="Analyst Alpha-7">Analyst Alpha-7</option>
            <option value="Analyst Beta-2">Analyst Beta-2</option>
            <option value="System Auth">System Auth</option>
          </select>

          <select 
            value={severityFilter} 
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{ background: '#0a101d', border: '1px solid var(--border-color)', color: 'var(--text-main)', padding: '6px 12px', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
          >
            <option value="All">All Severities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Nominal">Nominal</option>
          </select>

          <button className="btn-new-investigation" style={{ width: 'auto', background: '#162338', color: 'var(--text-main)', border: '1px solid var(--border-color)', boxShadow: 'none' }}>
            <Filter size={14} /> Filter
          </button>

          <button className="btn-new-investigation" style={{ width: 'auto', background: '#162338', color: 'var(--text-main)', border: '1px solid var(--border-color)', boxShadow: 'none' }} onClick={handleExportCSV}>
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
          <thead>
            <tr style={{ background: '#0a101d', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '12px 16px' }}>Timestamp (UTC)</th>
              <th style={{ padding: '12px 16px' }}>Operator ID</th>
              <th style={{ padding: '12px 16px' }}>Severity</th>
              <th style={{ padding: '12px 16px' }}>Action Logged</th>
              <th style={{ padding: '12px 16px' }}>SHA-256 Checksum (Trunc)</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, idx) => {
              const isHigh = log.severity === 'High';
              const isMed = log.severity === 'Medium';
              return (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>{log.timestamp}</td>
                  <td style={{ padding: '14px 16px', color: 'var(--accent-cyan)', fontWeight: '600' }}>{log.operatorId}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ color: isHigh ? 'var(--status-critical)' : isMed ? 'var(--status-high)' : 'var(--text-muted)' }}>
                      ● {log.severity}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', color: 'var(--text-bright)' }}>{log.actionLogged}</td>
                  <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>{log.checksum}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Footer Pagination */}
        <div style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          <div>Showing 5 of 12,408 records</div>

          <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
            <button className="topbar-icon-btn" style={{ padding: '4px' }}><ChevronLeft size={14} /></button>
            <span style={{ padding: '2px 8px', background: 'var(--accent-cyan)', color: '#070d17', borderRadius: '3px', fontWeight: '700' }}>1</span>
            <span style={{ padding: '2px 8px', color: 'var(--text-muted)' }}>2</span>
            <span style={{ padding: '2px 8px', color: 'var(--text-muted)' }}>3</span>
            <span>...</span>
            <button className="topbar-icon-btn" style={{ padding: '4px' }}><ChevronRight size={14} /></button>
          </div>
        </div>
      </div>
    </div>
  );
}
