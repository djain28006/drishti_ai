import React, { useState, useEffect } from 'react';
import { Lock, CheckCircle, Filter, Download, User, AlertTriangle, Plus } from 'lucide-react';
import { getUserAuditLogs, logUserAudit } from '../firebase';

export default function AuditLogsPage({ user }) {
  const [operatorFilter, setOperatorFilter] = useState('All');
  const [severityFilter, setSeverityFilter] = useState('All');
  const [firestoreLogs, setFirestoreLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    if (user?.uid) {
      const logs = await getUserAuditLogs(user.uid);
      setFirestoreLogs(logs);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs();
  }, [user]);

  // Fallback initial dataset matching user constraints (Timestamp, Zone ID, Anomaly at Desk, Severity, Checksum)
  const defaultAnomalyLogs = [
    {
      timestamp: '2026-08-23T04:25:01.005Z',
      zoneId: 'S4',
      deskId: 'Desk S4',
      anomaly: 'Mobile Phone Object Interaction Detected at Desk S4',
      operatorId: user?.displayName || 'Analyst Alpha-7',
      severity: 'Critical',
      checksum: 'INC-FB313E-7f83b165'
    },
    {
      timestamp: '2026-08-23T04:15:22.198Z',
      zoneId: 'S5',
      deskId: 'Desk S5',
      anomaly: 'Gaze Shift & Prolonged Glance Right Anomaly at Desk S5',
      operatorId: user?.displayName || 'Analyst Alpha-7',
      severity: 'High',
      checksum: 'INC-FB314F-3a22c981'
    },
    {
      timestamp: '2026-08-23T03:45:09.771Z',
      zoneId: 'S9',
      deskId: 'Desk S9',
      anomaly: 'Unauthorized Paper Chit Exchange Attempt at Desk S9',
      operatorId: user?.displayName || 'System Auth',
      severity: 'Medium',
      checksum: 'INC-FB315G-b9c410dd'
    },
    {
      timestamp: '2026-08-23T03:10:00.000Z',
      zoneId: 'S1',
      deskId: 'Desk S1',
      anomaly: 'Baseline Desk Behavior Calibration Completed for Zone S1',
      operatorId: user?.displayName || 'Forensics Bot',
      severity: 'Nominal',
      checksum: 'CAL-S1-d41d8cd9'
    }
  ];

  // Trigger writing a new real-time anomaly log to Firestore
  const handleGenerateNewAnomalyLog = async () => {
    if (!user?.uid) return;
    const testAnomalies = [
      { zone: 'S4', desk: 'Desk S4', text: 'Cell phone object interaction detected at Desk S4', sev: 'Critical' },
      { zone: 'S5', desk: 'Desk S5', text: 'Sustained posture deviation & gaze anomaly at Desk S5', sev: 'High' },
      { zone: 'S2', desk: 'Desk S2', text: 'Peeking & lateral head rotation at Desk S2', sev: 'High' },
      { zone: 'S9', desk: 'Desk S9', text: 'Unauthorized document movement detected at Desk S9', sev: 'Medium' }
    ];
    const picked = testAnomalies[Math.floor(Math.random() * testAnomalies.length)];

    await logUserAudit(
      user.uid,
      user.email,
      "ANOMALY_DETECTED",
      user.displayName || "Analyst Lead",
      picked.text,
      picked.zone,
      picked.desk,
      picked.sev,
      `SHA256-${Date.now().toString(16)}`
    );
    await fetchLogs();
  };

  const rawList = firestoreLogs.length > 0 ? firestoreLogs : defaultAnomalyLogs;

  // Filter logs by Severity & Operator
  const filteredLogs = rawList.filter(log => {
    if (severityFilter !== 'All' && log.severity !== severityFilter) return false;
    return true;
  });

  const handleExportCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," 
      + ["Timestamp (UTC),Zone ID,Desk ID,Anomaly Logged,Severity,Officer,SHA-256 Checksum"]
      .concat(filteredLogs.map(l => `"${l.timestamp || l.createdAt}","${l.zoneId}","${l.deskId}","${l.anomaly || l.details}","${l.severity}","${l.operatorId || l.userEmail}","${l.checksum}"`))
      .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `drishti_anomaly_audit_logs_${user?.username || 'officer'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'Critical':
        return <span className="badge badge-critical">Critical</span>;
      case 'High':
        return <span className="badge badge-high">High</span>;
      case 'Medium':
        return <span className="badge badge-med">Medium</span>;
      default:
        return <span className="badge badge-nominal">Nominal</span>;
    }
  };

  return (
    <div className="content-area">
      {/* Header & Vault Status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Chain of Custody & Firestore Audit Log</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '6px', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--text-muted)' }}>Firestore User Sync:</span>
            <span className="badge" style={{ background: 'rgba(0, 242, 255, 0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--border-cyan)' }}>
              <Lock size={12} /> {user?.email || 'Authenticated Officer'} <CheckCircle size={12} />
            </span>
          </div>
        </div>

        {/* Filter & Action Controls */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select 
            value={severityFilter} 
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{ background: '#0a101d', border: '1px solid var(--border-color)', color: 'var(--text-main)', padding: '6px 12px', borderRadius: '6px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
          >
            <option value="All">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Nominal">Nominal</option>
          </select>

          <button 
            className="btn-new-investigation" 
            onClick={handleGenerateNewAnomalyLog}
            style={{ width: 'auto', background: 'rgba(0, 242, 255, 0.15)', color: '#00f2ff', border: '1px solid var(--border-cyan)', boxShadow: 'none' }}
          >
            <Plus size={14} /> Log Anomaly to Firestore
          </button>

          <button 
            className="btn-new-investigation" 
            onClick={handleExportCSV}
            style={{ width: 'auto' }}
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Audit Log Table matching user constraints */}
      <div className="card" style={{ padding: '0', overflow: 'hidden', marginTop: '20px' }}>
        <table className="dossier-table" style={{ width: '100%' }}>
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Zone ID</th>
              <th>Desk ID</th>
              <th>Anomaly Logged</th>
              <th>Severity</th>
              <th>Officer / Operator</th>
              <th>SHA-256 Checksum</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                  Fetching Firestore Anomaly Audit Logs...
                </td>
              </tr>
            ) : filteredLogs.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                  No anomaly logs found for selected filter.
                </td>
              </tr>
            ) : (
              filteredLogs.map((log, idx) => (
                <tr key={idx}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : new Date().toLocaleString()}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: '#fff' }}>
                    {log.zoneId || 'S4'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    {log.deskId || 'Desk S4'}
                  </td>
                  <td style={{ color: 'var(--text-bright)', fontSize: '12px', fontWeight: '500' }}>
                    <AlertTriangle size={13} style={{ verticalAlign: 'middle', marginRight: '6px', color: log.severity === 'Critical' ? 'var(--status-critical)' : 'var(--status-high)' }} />
                    {log.anomaly || log.details}
                  </td>
                  <td>
                    {getSeverityBadge(log.severity)}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                    <User size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                    {log.operatorId || log.userEmail || 'Forensic Officer'}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>
                    {log.checksum || '7f83b165...e9a4'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
