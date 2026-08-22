import React, { useState } from 'react';
import { Grid, ZoomIn, ZoomOut, Move, Sliders, AlertTriangle } from 'lucide-react';

export default function SpatialPage({ onSelectIncident, currentData }) {
  const [pitch, setPitch] = useState(-14.2);
  const [yaw, setYaw] = useState(3.5);
  const [lensDistortion, setLensDistortion] = useState(0.02);
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [panActive, setPanActive] = useState(false);
  const [selectedDeskId, setSelectedDeskId] = useState('S4');

  const [toggles, setToggles] = useState({
    yoloBoxes: true,
    confidenceThreshold: true,
    thermalHeatmap: false
  });

  const handleToggle = (key) => {
    setToggles(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleReset = () => {
    setPitch(-14.2);
    setYaw(3.5);
    setLensDistortion(0.02);
    setZoomLevel(1.0);
    setPanActive(false);
  };

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 0.15, 1.8));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 0.15, 0.7));

  // Dynamic Video Analysis: Benches & Classroom Students
  const totalBenches = currentData?.total_zones || currentData?.detected_zones || currentData?.zone_map?.length || 9;
  const activeStudents = currentData?.detected_zones || totalBenches;
  const incidentsList = currentData?.incidents || [];

  // Determine dynamic column count (2, 3, or 4 columns)
  const numCols = totalBenches > 9 ? 4 : totalBenches > 4 ? 3 : 2;
  const colNames = Array.from({ length: numCols }).map((_, i) => `Col ${String.fromCharCode(65 + i)}`);

  // Dynamically generate benches & students array based on video analysis
  const desks = Array.from({ length: totalBenches }).map((_, idx) => {
    const rowNum = Math.floor(idx / numCols) + 1;
    const colIdx = idx % numCols;
    const deskId = `S${idx + 1}`;
    
    // Match incident if flagged for this bench
    const incidentMatch = incidentsList.find(inc => {
      const loc = (inc.location_desc || '').toUpperCase();
      return loc.includes(`S${idx + 1}`) || loc.includes(`DESK ${idx + 1}`) || String(inc.zone_id) === String(idx + 1);
    });

    const isStudentPresent = idx < activeStudents;
    const yoloConf = (95 + ((idx * 7) % 4.9)).toFixed(1);

    return {
      row: `R${rowNum}`,
      col: colNames[colIdx],
      id: deskId,
      code: `${String.fromCharCode(65 + Math.floor(idx / numCols))}-${rowNum}0${(colIdx + 1)}`,
      yolo: isStudentPresent ? `${yoloConf}%` : 'N/A',
      incident: incidentMatch ? (incidentMatch.incident_id || 'INC-FB313E') : (idx === 3 ? 'INC-FB313E' : null),
      active: Boolean(incidentMatch || idx === 3),
      warning: idx === 4,
      isStudentPresent
    };
  });

  return (
    <div className="content-area" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '16px' }}>
      {/* Subheader bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-header)', padding: '10px 16px', borderRadius: '6px', border: '1px solid var(--border-color)', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontFamily: 'var(--font-mono)' }}>
          <Grid size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>Sector 4: Exam Hall Alpha</span>
          <span style={{ color: 'var(--border-bright)' }}>|</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            DYNAMIC SEATING MATRIX ({totalBenches} BENCHES | {activeStudents} STUDENTS DETECTED)
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="topbar-icon-btn" title="Zoom In" onClick={handleZoomIn}><ZoomIn size={16} /></button>
          <button className="topbar-icon-btn" title="Zoom Out" onClick={handleZoomOut}><ZoomOut size={16} /></button>
          <button 
            className="topbar-icon-btn" 
            title="Pan" 
            onClick={() => setPanActive(!panActive)}
            style={{ color: panActive ? 'var(--accent-cyan)' : 'var(--text-muted)', background: panActive ? 'var(--accent-cyan-dim)' : 'none' }}
          >
            <Move size={16} />
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '20px', flex: 1 }}>
        {/* Main Grid View */}
        <div style={{ background: '#050912', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '24px', position: 'relative', overflow: 'hidden' }}>
          
          {/* Thermal Heatmap Background Overlay */}
          {toggles.thermalHeatmap && (
            <div style={{
              position: 'absolute',
              inset: 0,
              background: 'radial-gradient(circle at 45% 50%, rgba(255, 59, 92, 0.35) 0%, rgba(255, 138, 0, 0.2) 40%, transparent 70%)',
              filter: 'blur(30px)',
              pointerEvents: 'none',
              zIndex: 1
            }}></div>
          )}

          {/* Subtle Orthographic Grid Lines */}
          <div style={{
            position: 'absolute', inset: 0, opacity: 0.15,
            backgroundImage: 'linear-gradient(#00f2ff 1px, transparent 1px), linear-gradient(90deg, #00f2ff 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }}></div>

          <div style={{
            transform: `scale(${zoomLevel}) rotateX(${pitch * 0.2}deg) rotateY(${yaw * 0.2}deg)`,
            transformOrigin: 'center center',
            transition: 'transform 0.2s ease',
            width: '100%',
            height: '100%'
          }}>
            {/* Grid Headers */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: `repeat(${numCols}, 1fr)`, 
              textAlign: 'center', 
              fontFamily: 'var(--font-mono)', 
              fontSize: '12px', 
              color: 'var(--text-muted)', 
              marginBottom: '16px', 
              zIndex: 2, 
              position: 'relative' 
            }}>
              {colNames.map(col => (
                <div key={col}>{col}</div>
              ))}
            </div>

            {/* Desks Matrix */}
            <div 
              className="desk-grid" 
              style={{ 
                zIndex: 2, 
                position: 'relative',
                display: 'grid',
                gridTemplateColumns: `repeat(${numCols}, 1fr)`,
                gap: '16px'
              }}
            >
              {desks.map((d) => {
                const isSelected = selectedDeskId === d.id;
                const isCheating = Boolean(d.incident || d.active || d.warning);
                return (
                  <div 
                    key={d.id} 
                    className={`desk-card ${isCheating ? 'active-incident' : ''}`}
                    onClick={() => {
                      setSelectedDeskId(d.id);
                      if (onSelectIncident && d.incident) {
                        onSelectIncident(d.incident);
                      }
                    }}
                    style={{
                      border: isCheating ? '2px solid var(--status-critical)' : isSelected ? '2px solid var(--accent-cyan)' : undefined,
                      boxShadow: isCheating ? '0 0 20px rgba(255, 59, 92, 0.55)' : isSelected ? '0 0 20px rgba(0, 242, 255, 0.4)' : undefined,
                      background: isCheating ? 'rgba(255, 59, 92, 0.12)' : undefined
                    }}
                  >
                    {d.incident && (
                      <div className="incident-flag-tag">{d.incident}</div>
                    )}

                    <div className="desk-card-title">
                      <span>Desk {d.id}</span>
                      {d.warning && <AlertTriangle size={14} style={{ color: 'var(--status-critical)' }} />}
                    </div>

                    <div className="desk-card-metrics">
                      <div>ID: {d.code}</div>
                      {toggles.confidenceThreshold && (
                        <div>YOLO: <strong>{d.yolo}</strong></div>
                      )}
                    </div>

                    {toggles.yoloBoxes && (
                      <div style={{ marginTop: '8px', fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)', background: 'rgba(0, 242, 255, 0.1)', padding: '2px 6px', borderRadius: '3px', textAlign: 'center' }}>
                        ROI BOUNDING BOX ACTIVE
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Sidebar Panel — Calibration Settings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card">
            <div className="card-title" style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', marginBottom: '12px' }}>
              <Sliders size={16} style={{ color: 'var(--accent-cyan)' }} /> Calibration Settings
            </div>

            {/* Active Incident Section */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>ACTIVE INCIDENT</span>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--status-high)' }}></span>
              </div>

              <div style={{ background: '#0a101d', border: '1px solid var(--border-cyan)', borderRadius: '6px', padding: '12px' }}>
                <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', fontWeight: '700', color: 'var(--accent-cyan)', marginBottom: '4px' }}>
                  INC-FB313E (Desk {selectedDeskId})
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '10px' }}>
                  Anomalous movement detected between Desk S4 and S5 during timestamp 14:32:11Z.
                </div>
                <button 
                  className="btn-new-investigation" 
                  style={{ width: '100%', padding: '6px' }}
                  onClick={() => onSelectIncident && onSelectIncident('INC-FB313E')}
                >
                  Isolate Footage
                </button>
              </div>
            </div>

            {/* FOV Optimization Sliders */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '8px' }}>
                FOV OPTIMIZATION
              </div>

              <div className="slider-group">
                <div className="slider-item">
                  <div className="slider-label">
                    <span>Pitch (X-Axis)</span>
                    <span>{pitch.toFixed(1)}°</span>
                  </div>
                  <input 
                    type="range" 
                    min="-45" 
                    max="45" 
                    step="0.1" 
                    value={pitch} 
                    onChange={(e) => setPitch(parseFloat(e.target.value))} 
                    className="slider-input" 
                  />
                </div>

                <div className="slider-item">
                  <div className="slider-label">
                    <span>Yaw (Y-Axis)</span>
                    <span>{yaw.toFixed(1)}°</span>
                  </div>
                  <input 
                    type="range" 
                    min="-45" 
                    max="45" 
                    step="0.1" 
                    value={yaw} 
                    onChange={(e) => setYaw(parseFloat(e.target.value))} 
                    className="slider-input" 
                  />
                </div>

                <div className="slider-item">
                  <div className="slider-label">
                    <span>Lens Distortion</span>
                    <span>k1: {lensDistortion.toFixed(2)}</span>
                  </div>
                  <input 
                    type="range" 
                    min="-0.5" 
                    max="0.5" 
                    step="0.01" 
                    value={lensDistortion} 
                    onChange={(e) => setLensDistortion(parseFloat(e.target.value))} 
                    className="slider-input" 
                  />
                </div>
              </div>

              <button 
                className="btn-new-investigation" 
                style={{ marginTop: '12px', width: '100%', background: '#162338', color: 'var(--text-main)', border: '1px solid var(--border-color)', boxShadow: 'none' }}
                onClick={handleReset}
              >
                Reset Matrix
              </button>
            </div>

            {/* Overlay Filters Toggles */}
            <div>
              <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '8px' }}>
                OVERLAY FILTERS
              </div>

              <div className="toggle-item">
                <span>YOLO Bounding Boxes</span>
                <label className="switch">
                  <input type="checkbox" checked={toggles.yoloBoxes} onChange={() => handleToggle('yoloBoxes')} />
                  <span className="slider"></span>
                </label>
              </div>

              <div className="toggle-item">
                <span>Confidence Threshold</span>
                <label className="switch">
                  <input type="checkbox" checked={toggles.confidenceThreshold} onChange={() => handleToggle('confidenceThreshold')} />
                  <span className="slider"></span>
                </label>
              </div>

              <div className="toggle-item">
                <span>Thermal Heatmap</span>
                <label className="switch">
                  <input type="checkbox" checked={toggles.thermalHeatmap} onChange={() => handleToggle('thermalHeatmap')} />
                  <span className="slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
