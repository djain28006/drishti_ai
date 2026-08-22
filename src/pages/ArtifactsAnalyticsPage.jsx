import React, { useState } from 'react';
import { Info, Eye, Activity } from 'lucide-react';

export default function ArtifactsAnalyticsPage() {
  const [timeRange, setTimeRange] = useState('1H');

  return (
    <div className="content-area">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Activity Analytics</h1>
          <p className="page-subtitle">Real-time surveillance telemetry and behavioral heatmaps.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent-cyan)' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-cyan)', boxShadow: '0 0 10px var(--accent-cyan)' }}></span>
          LIVE FEED ACTIVE
        </div>
      </div>

      {/* Grid: Suspicion Map & Optical Motion Density */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Card 1: Baseline Desk Suspicion Map */}
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: '600', color: 'var(--text-bright)' }}>
              Baseline-Normalized Desk Suspicion Map
            </span>
            <Info size={16} style={{ color: 'var(--text-muted)', cursor: 'pointer' }} />
          </div>

          <div style={{ height: '320px', background: '#050912', position: 'relative', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {/* Tactical Grid floorplan background */}
            <svg width="100%" height="100%" style={{ position: 'absolute', opacity: 0.25 }}>
              <defs>
                <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#00f2ff" strokeWidth="0.5" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>

            {/* Simulated Seating Layout Overlay */}
            <div style={{ position: 'relative', width: '85%', height: '80%', border: '1px stroke rgba(0,242,255,0.2)', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', padding: '16px' }}>
              {Array.from({ length: 12 }).map((_, idx) => {
                const isHighRisk = idx === 4 || idx === 5;
                const isMedRisk = idx === 8;
                return (
                  <div 
                    key={idx} 
                    style={{ 
                      border: `1px solid ${isHighRisk ? 'var(--status-critical)' : isMedRisk ? 'var(--status-high)' : 'var(--border-bright)'}`,
                      background: isHighRisk ? 'rgba(255, 59, 92, 0.15)' : isMedRisk ? 'rgba(255, 138, 0, 0.15)' : 'rgba(0, 242, 255, 0.05)',
                      borderRadius: '4px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justify: 'center',
                      padding: '8px',
                      boxShadow: isHighRisk ? '0 0 15px rgba(255, 59, 92, 0.4)' : isMedRisk ? '0 0 10px rgba(255, 138, 0, 0.3)' : 'none'
                    }}
                  >
                    <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>DESK S{idx+1}</span>
                    <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', fontWeight: '700', color: isHighRisk ? 'var(--status-critical)' : isMedRisk ? 'var(--status-high)' : 'var(--accent-cyan)' }}>
                      {isHighRisk ? '98.4% RISK' : isMedRisk ? '64.2%' : '12.0%'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Card 2: Global MOG2 Optical Motion Density */}
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: '600', color: 'var(--text-bright)' }}>
              Global MOG2 Optical Motion Density
            </span>
            <Eye size={16} style={{ color: 'var(--text-muted)', cursor: 'pointer' }} />
          </div>

          <div style={{ height: '320px', background: '#070b14', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {/* Checkerboard Pattern */}
            <div style={{
              position: 'absolute',
              inset: 0,
              backgroundImage: `linear-gradient(45deg, #0d1424 25%, transparent 25%), linear-gradient(-45deg, #0d1424 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #0d1424 75%), linear-gradient(-45deg, transparent 75%, #0d1424 75%)`,
              backgroundSize: '24px 24px',
              backgroundPosition: '0 0, 0 12px, 12px -12px, -12px 0px',
              opacity: 0.4
            }}></div>

            {/* Glowing Motion Density Blob */}
            <div style={{
              width: '180px',
              height: '180px',
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(0, 242, 255, 0.4) 0%, rgba(255, 59, 92, 0.3) 50%, transparent 70%)',
              filter: 'blur(20px)',
              position: 'absolute'
            }}></div>

            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              fontWeight: '700',
              color: 'rgba(0, 242, 255, 0.4)',
              letterSpacing: '6px',
              transform: 'rotate(-25deg)',
              userSelect: 'none',
              zIndex: 2
            }}>
              MOTION _ DATA _ STREAM
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Panel: Behavioral Trend Chart */}
      <div className="card">
        <div className="card-header" style={{ marginBottom: '8px' }}>
          <div className="card-title" style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
            <Activity size={16} style={{ color: 'var(--accent-cyan)' }} /> Behavioral Trend: Deviation Frequency vs Time
          </div>

          <div style={{ display: 'flex', gap: '4px' }}>
            {['1H', '12H', '24H'].map(range => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                style={{
                  background: timeRange === range ? 'var(--accent-cyan)' : 'var(--bg-darkest)',
                  color: timeRange === range ? '#070d17' : 'var(--text-muted)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '4px',
                  padding: '4px 10px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {/* Wave Graph SVG */}
        <div style={{ height: '220px', width: '100%', position: 'relative', paddingTop: '10px' }}>
          <svg width="100%" height="100%" viewBox="0 0 800 200" preserveAspectRatio="none">
            {/* Grid lines */}
            <line x1="0" y1="50" x2="800" y2="50" stroke="#172338" strokeDasharray="4" />
            <line x1="0" y1="100" x2="800" y2="100" stroke="#172338" strokeDasharray="4" />
            <line x1="0" y1="150" x2="800" y2="150" stroke="#172338" strokeDasharray="4" />

            {/* Baseline Activity Curve (Solid Cyan) */}
            <path
              d="M 0 160 Q 150 150 300 120 T 600 80 T 800 140"
              fill="none"
              stroke="#00f2ff"
              strokeWidth="4"
            />

            {/* Anomalous Deviations Curve (Dashed Coral Red) */}
            <path
              d="M 0 180 Q 200 180 400 170 T 700 40 T 800 180"
              fill="none"
              stroke="#ff3b5c"
              strokeWidth="4"
              strokeDasharray="8 6"
            />
          </svg>

          {/* Y Axis labels */}
          <div style={{ position: 'absolute', top: 0, left: 10, fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-dim)' }}>100</div>
          <div style={{ position: 'absolute', top: 90, left: 10, fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-dim)' }}>50</div>
          <div style={{ position: 'absolute', bottom: 10, left: 10, fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-dim)' }}>0</div>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '24px', marginTop: '12px', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
            <span style={{ width: '16px', height: '3px', background: '#00f2ff' }}></span>
            Baseline Activity
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
            <span style={{ width: '16px', height: '3px', background: '#ff3b5c', borderStyle: 'dashed' }}></span>
            Anomalous Deviations
          </div>
        </div>
      </div>
    </div>
  );
}
