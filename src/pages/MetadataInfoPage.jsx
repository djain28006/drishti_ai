import React from 'react';
import { Activity, Server, Shield, Cpu } from 'lucide-react';

export default function MetadataInfoPage() {
  return (
    <div className="content-area">
      <div>
        <h1 className="page-title">Forensic Engine Metadata & System Health</h1>
        <p className="page-subtitle">Model Weights, Algorithm Parameters & Local Engine Diagnostics</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div className="card">
          <div className="card-title" style={{ color: 'var(--accent-cyan)', marginBottom: '14px' }}>
            <Cpu size={18} /> Model Configuration
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Object Detection Backbone:</span>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: '700' }}>Custom Trained Detector (best.pt)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Motion Estimation Algorithm:</span>
              <span style={{ color: '#fff' }}>OpenCV MOG2 Subtractor</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Baseline Anomaly Engine:</span>
              <span style={{ color: '#fff' }}>Z-Score Normalized Moving Average</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
              <span style={{ color: 'var(--text-muted)' }}>Cross-Camera Fusion:</span>
              <span style={{ color: '#fff' }}>IOU & Time-Window Fusion</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ color: 'var(--status-nominal)', marginBottom: '14px' }}>
            <Server size={18} /> System Status
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>FastAPI Engine:</span>
              <span style={{ color: 'var(--status-nominal)' }}>ONLINE (Port 8000)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)' }}>GPU Acceleration:</span>
              <span style={{ color: 'var(--accent-cyan)' }}>MPS / CUDA Active</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
              <span style={{ color: 'var(--text-muted)' }}>Vault Storage Mode:</span>
              <span style={{ color: '#fff' }}>Local Encrypted SQLite DB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
