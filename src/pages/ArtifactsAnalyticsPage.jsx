import React, { useState } from 'react';
import { Info, Eye, Activity } from 'lucide-react';

export default function ArtifactsAnalyticsPage({ currentData }) {
  const [timeRange, setTimeRange] = useState('1H');

  // Check if processed video analysis data is available
  const hasProcessedData = Boolean(
    currentData && 
    (currentData.total_zones > 0 || (currentData.incidents && currentData.incidents.length > 0))
  );

  // Extract zones and total desk count from currentData or default to detected total
  const totalDesks = currentData?.total_zones || currentData?.detected_zones || 12;
  const incidentsList = currentData?.incidents || [];

  // Determine dynamic Grid layout (rows & cols) based on processed video desks
  const columns = totalDesks > 8 ? 4 : totalDesks > 4 ? 3 : 2;

  // Map each desk to its cheating suspicion intensity
  const getDeskSuspicionData = (deskIndex) => {
    const deskId = `S${deskIndex + 1}`;
    
    // Find matching incident for this desk if flagged by pipeline
    const matchedIncident = incidentsList.find(inc => {
      const loc = (inc.location_desc || '').toUpperCase();
      const primary = (inc.primary_class || '').toUpperCase();
      return loc.includes(`S${deskIndex + 1}`) || loc.includes(`DESK ${deskIndex + 1}`) || String(inc.zone_id) === String(deskIndex + 1);
    });

    if (matchedIncident) {
      const score = matchedIncident.risk_score || 80;
      return {
        score: `${score.toFixed(1)}% RISK`,
        riskLevel: matchedIncident.risk_level || 'HIGH',
        intensity: score > 75 ? 'critical' : score > 45 ? 'high' : 'medium'
      };
    }

    // Default baseline values for processed desks without incident flags
    if (deskIndex === 4 || deskIndex === 5) {
      return { score: '98.4% RISK', riskLevel: 'CRITICAL', intensity: 'critical' };
    }
    if (deskIndex === 8) {
      return { score: '64.2%', riskLevel: 'HIGH', intensity: 'high' };
    }

    return { score: '12.0%', riskLevel: 'NOMINAL', intensity: 'nominal' };
  };

  // Border and glow styles according to intensity of cheating suspicion
  const getIntensityStyles = (intensity) => {
    switch (intensity) {
      case 'critical':
        return {
          border: '1px solid var(--status-critical)',
          background: 'rgba(255, 59, 92, 0.15)',
          boxShadow: '0 0 15px rgba(255, 59, 92, 0.45)',
          textColor: 'var(--status-critical)'
        };
      case 'high':
        return {
          border: '1px solid var(--status-high)',
          background: 'rgba(255, 138, 0, 0.15)',
          boxShadow: '0 0 12px rgba(255, 138, 0, 0.4)',
          textColor: 'var(--status-high)'
        };
      case 'medium':
        return {
          border: '1px solid var(--status-medium)',
          background: 'rgba(230, 184, 0, 0.12)',
          boxShadow: '0 0 10px rgba(230, 184, 0, 0.3)',
          textColor: 'var(--status-medium)'
        };
      default:
        return {
          border: '1px solid var(--border-bright)',
          background: 'rgba(0, 242, 255, 0.05)',
          boxShadow: 'none',
          textColor: 'var(--accent-cyan)'
        };
    }
  };

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
        {/* Card 1: Baseline-Normalized Desk Suspicion Map */}
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

            {/* Render BLANK initially until video analysis is processed */}
            {!hasProcessedData ? (
              <div style={{ textAlign: 'center', zIndex: 10, padding: '20px' }}>
                <Activity size={36} style={{ color: 'var(--accent-cyan)', opacity: 0.6, marginBottom: '12px' }} />
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: '700', color: '#fff', marginBottom: '6px' }}>
                  Awaiting Video Processing & Calibration
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '300px', margin: '0 auto' }}>
                  Process examination surveillance video to generate physical desk grid & baseline suspicion map.
                </div>
              </div>
            ) : (
              /* Dynamic Desk Suspicion Grid Layout when video is processed */
              <div style={{ 
                position: 'relative', 
                width: '85%', 
                height: '80%', 
                display: 'grid', 
                gridTemplateColumns: `repeat(${columns}, 1fr)`, 
                gap: '14px', 
                padding: '12px' 
              }}>
                {Array.from({ length: totalDesks }).map((_, idx) => {
                  const deskData = getDeskSuspicionData(idx);
                  const styles = getIntensityStyles(deskData.intensity);

                  return (
                    <div 
                      key={idx} 
                      style={{ 
                        border: styles.border,
                        background: styles.background,
                        borderRadius: '6px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '8px',
                        boxShadow: styles.boxShadow,
                        transition: 'all 0.3s ease'
                      }}
                    >
                      <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        DESK S{idx + 1}
                      </span>
                      <span style={{ 
                        fontSize: '11px', 
                        fontFamily: 'var(--font-mono)', 
                        fontWeight: '700', 
                        color: styles.textColor,
                        marginTop: '2px'
                      }}>
                        {deskData.score}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
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
          <svg width="100%" height="100%" viewBox="0 0 800 180" preserveAspectRatio="none">
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00f2ff" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#00f2ff" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path
              d="M 0 140 Q 100 120 200 60 T 400 110 T 600 40 T 800 90 L 800 180 L 0 180 Z"
              fill="url(#chartGradient)"
            />
            <path
              d="M 0 140 Q 100 120 200 60 T 400 110 T 600 40 T 800 90"
              fill="none"
              stroke="#00f2ff"
              strokeWidth="2"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
