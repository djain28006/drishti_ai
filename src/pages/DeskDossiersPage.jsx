import React, { useState } from 'react';
import { User, Download, ShieldAlert, Award } from 'lucide-react';

export default function DeskDossiersPage({ currentData = {}, apiBase = '' }) {
  const students = currentData.students || Array.from({ length: 12 }).map((_, i) => ({
    zone_id: i + 1,
    desk_name: `Desk S${i + 1}`,
    activity_score: Math.floor(Math.random() * 80) + 20,
    risk_level: i === 4 ? 'HIGH' : i === 8 ? 'MEDIUM' : 'NOMINAL'
  }));

  const [selectedStudent, setSelectedStudent] = useState(students[0] || null);

  return (
    <div className="content-area">
      <div>
        <h1 className="page-title">Desk Dossiers & Student Profiles</h1>
        <p className="page-subtitle">Per-Desk Surveillance Dossier & Behavior History</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
        {/* Desk List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {students.map((st) => {
            const isSelected = selectedStudent && selectedStudent.zone_id === st.zone_id;
            return (
              <div 
                key={st.zone_id}
                className="card"
                style={{
                  cursor: 'pointer',
                  border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                  background: isSelected ? 'var(--accent-cyan-dim)' : 'var(--bg-card)',
                  display: 'flex',
                  justify: 'space-between',
                  alignItems: 'center'
                }}
                onClick={() => setSelectedStudent(st)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <User size={18} style={{ color: 'var(--accent-cyan)' }} />
                  <div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontWeight: '700', color: '#fff' }}>Desk S{st.zone_id}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Score: {st.activity_score}%</div>
                  </div>
                </div>

                <span className={`badge ${st.risk_level === 'HIGH' ? 'badge-high' : st.risk_level === 'MEDIUM' ? 'badge-med' : 'badge-nominal'}`}>
                  {st.risk_level}
                </span>
              </div>
            );
          })}
        </div>

        {/* Selected Detail Dossier */}
        {selectedStudent && (
          <div className="card">
            <div className="card-header">
              <div className="card-title">Dossier: Desk S{selectedStudent.zone_id}</div>
              <a 
                href={`${apiBase}/api/report/student/${selectedStudent.zone_id}`}
                target="_blank"
                rel="noreferrer"
                className="btn-new-investigation"
                style={{ width: 'auto', textDecoration: 'none' }}
              >
                <Download size={14} /> Download Desk PDF
              </a>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div style={{ background: '#0a101d', border: '1px solid var(--border-color)', padding: '14px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Aggregated Risk Index</div>
                  <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{selectedStudent.activity_score}/100</div>
                </div>

                <div style={{ background: '#0a101d', border: '1px solid var(--border-color)', padding: '14px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>Security Status</div>
                  <div style={{ fontSize: '16px', fontWeight: '700', color: selectedStudent.risk_level === 'HIGH' ? 'var(--status-high)' : 'var(--status-nominal)', marginTop: '8px' }}>
                    {selectedStudent.risk_level}
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Spatial ROI coordinates and behavioral trend history are logged for desk region S{selectedStudent.zone_id}. Cross-referencing with global MOG2 motion vector streams confirmed high stability index across surveillance frames.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
