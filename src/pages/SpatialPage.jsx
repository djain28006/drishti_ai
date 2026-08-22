import React, { useState } from 'react';
import { Grid, ZoomIn, ZoomOut, Move, Sliders, AlertTriangle } from 'lucide-react';

export default function SpatialPage({ onSelectIncident }) {
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

  const desks = [
    { row: 'R1', col: 'Col A', id: 'S1', code: 'A-101', yolo: '99.1%' },
    { row: 'R1', col: 'Col B', id: 'S2', code: 'A-102', yolo: '98.4%' },
    { row: 'R1', col: 'Col C', id: 'S3', code: 'A-103', yolo: '97.8%' },
    { row: 'R2', col: 'Col A', id: 'S4', code: 'B-201', yolo: '84.2%', incident: 'INC-FB313E', active: true },
    { row: 'R2', col: 'Col B', id: 'S5', code: 'B-202', yolo: '81.9%', active: true, warning: true },
    { row: 'R2', col: 'Col C', id: 'S6', code: 'B-203', yolo: '96.5%' },
    { row: 'R3', col: 'Col A', id: 'S7', code: 'C-301', yolo: '99.9%' },
    { row: 'R3', col: 'Col B', id: 'S8', code: 'C-302', yolo: '98.1%' },
    { row: 'R3', col: 'Col C', id: 'S9', code: 'C-303', yolo: '97.2%' },
  ];

  return (
    <div className="content-area" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '16px' }}>
      {/* Subheader bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-header)', padding: '10px 16px', borderRadius: '6px', border: '1px solid var(--border-color)', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontFamily: 'var(--font-mono)' }}>
          <Grid size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span style={{ fontSize: '14px', fontWeight: '700', color: '#fff' }}>Sector 4: Exam Hall Alpha</span>
          <span style={{ color: 'var(--border-bright)' }}>|</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ORTHOGRAPHIC PROJECTION (Zoom: {(zoomLevel * 100).toFixed(0)}%)</span>
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
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px', zIndex: 2, position: 'relative' }}>
              <div>Col A</div>
              <div>Col B</div>
              <div>Col C</div>
            </div>

            {/* Desks Matrix */}
            <div className="desk-grid" style={{ zIndex: 2, position: 'relative' }}>
              {desks.map((d) => {
                const isSelected = selectedDeskId === d.id;
                return (
                  <div 
                    key={d.id} 
                    className={`desk-card ${d.active || isSelected ? 'active-incident' : ''}`}
                    onClick={() => {
                      setSelectedDeskId(d.id);
                      if (onSelectIncident && d.incident) {
                        onSelectIncident(d.incident);
                      }
                    }}
                    style={{
                      border: isSelected ? '2px solid var(--accent-cyan)' : undefined,
                      boxShadow: isSelected ? '0 0 20px rgba(0, 242, 255, 0.4)' : undefined
                    }}
                  >
                    {d.incident && (
                      <div className="incident-flag-tag">{d.incident}</div>
                    )}

                    <div className="desk-card-title">
                      <span>Desk {d.id}</span>
                      {d.warning && <AlertTriangle size={14} style={{ color: 'var(--accent-cyan)' }} />}
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
