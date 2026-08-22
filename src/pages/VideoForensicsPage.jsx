import React, { useState, useRef } from 'react';
import { Film, AlertTriangle, ShieldAlert, CheckCircle, Play, Eye, Maximize2, Volume2, VolumeX } from 'lucide-react';

export default function VideoForensicsPage({ currentData = {}, onOpenModal, apiBase = '' }) {
  const [activeTab, setActiveTab] = useState('All');
  const [selectedDesk, setSelectedDesk] = useState('S9');
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(true);
  const videoRef = useRef(null);

  const incidents = currentData.incidents || [
    {
      incident_id: 'INC-FB313E',
      risk_level: 'HIGH',
      risk_score: 80,
      duration_seconds: 8.75,
      location_desc: 'Desk S5 / S9',
      primary_class: 'Phone Detection'
    }
  ];

  const currentInc = incidents[0] || {};
  const clipUrl = `${apiBase}/api/media/clip/${encodeURIComponent(currentInc.incident_id || 'c6be8eb2')}`;

  const seekToTime = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  return (
    <div className="content-area" style={{ padding: '16px', gap: '16px' }}>
      {/* Top Telemetry Engine Bar */}
      <div style={{
        background: 'var(--bg-header)',
        border: '1px solid var(--border-color)',
        borderRadius: '6px',
        padding: '10px 16px',
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        fontFamily: 'var(--font-mono)',
        fontSize: '11px',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: 'var(--status-critical)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            ● LIVE LOCAL ENGINE
          </span>
          <span style={{ color: 'var(--border-bright)' }}>|</span>
          <span style={{ color: '#fff' }}>CCTV_HALL_B4_2026-08-22.mp4 | 1080p 24fps</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <strong>69</strong> Raw Triggers → <strong style={{ color: 'var(--accent-cyan)' }}>11</strong> Verified → <strong style={{ color: 'var(--status-high)' }}>10</strong> Deviations → <strong style={{ color: 'var(--status-critical)' }}>1</strong> Incident
          </div>
          <span style={{ color: 'var(--border-bright)' }}>|</span>
          <div style={{ color: 'var(--accent-cyan)' }}>88% Fatigue Reduction</div>
          <span style={{ color: 'var(--border-bright)' }}>|</span>
          <div>Session: 09.79s</div>
        </div>
      </div>

      {/* Main 2-Column Inspector Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '16px', flex: 1 }}>
        {/* Left Column: Incident List & Anomaly Breakdown */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Category Filter Tabs */}
          <div style={{ display: 'flex', gap: '6px', background: 'var(--bg-darkest)', padding: '4px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            {['All', 'Multi-Student', 'Phone', 'Peeking'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  flex: 1,
                  padding: '6px',
                  background: activeTab === tab ? 'var(--bg-card)' : 'transparent',
                  color: activeTab === tab ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  border: activeTab === tab ? '1px solid var(--border-cyan)' : 'none',
                  borderRadius: '4px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Active Incident Card */}
          <div 
            className="card" 
            style={{ border: '1px solid var(--border-cyan)', background: 'rgba(0, 242, 255, 0.03)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: '800', color: 'var(--status-critical)' }}>
                {currentInc.incident_id || 'INC-FB313E'}
              </span>
              <span className="badge badge-high">HIGH PRIORITY</span>
            </div>

            <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Risk: <strong style={{ color: 'var(--status-high)' }}>80/100</strong> | Duration: {currentInc.duration_seconds || 8.75}s
            </div>

            {/* Interactive Desk Breakdown Table */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '12px' }}>
              {[
                { desk: 'S5', label: 'Prolonged Glance Right 94%', risk: 'critical', seek: 1.5 },
                { desk: 'S6', label: 'Micro-gesture sync 82%', risk: 'high', seek: 3.2 },
                { desk: 'S9', label: 'Phone detected (pocket) 98%', risk: 'critical', seek: 5.0 },
                { desk: 'S7', label: 'Nominal 12%', risk: 'nominal', seek: 0.5 }
              ].map(item => (
                <div 
                  key={item.desk}
                  onClick={() => {
                    setSelectedDesk(item.desk);
                    seekToTime(item.seek);
                  }}
                  style={{
                    display: 'flex',
                    justify: 'space-between',
                    padding: '8px 10px',
                    background: selectedDesk === item.desk ? 'rgba(0, 242, 255, 0.12)' : '#0a111f',
                    borderRadius: '4px',
                    borderLeft: `3px solid ${item.risk === 'critical' ? 'var(--status-critical)' : item.risk === 'high' ? 'var(--status-high)' : 'var(--status-nominal)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <span style={{ fontWeight: selectedDesk === item.desk ? '700' : '400', color: selectedDesk === item.desk ? 'var(--accent-cyan)' : '#fff' }}>
                    Desk {item.desk}
                  </span>
                  <span style={{ color: item.risk === 'critical' ? 'var(--status-critical)' : item.risk === 'high' ? 'var(--status-high)' : 'var(--status-nominal)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                    {item.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Math Factor Attribution */}
            <div>
              <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '6px' }}>
                MATH FACTOR ATTRIBUTION
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                <span style={{ background: 'rgba(0, 242, 255, 0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--border-cyan)', padding: '2px 6px', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: '700' }}>
                  +25 Motion
                </span>
                <span style={{ background: 'rgba(255, 138, 0, 0.15)', color: 'var(--status-high)', border: '1px solid rgba(255, 138, 0, 0.4)', padding: '2px 6px', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: '700' }}>
                  +18 Gaze
                </span>
                <span style={{ background: 'rgba(255, 59, 92, 0.15)', color: 'var(--status-critical)', border: '1px solid rgba(255, 59, 92, 0.4)', padding: '2px 6px', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: '700' }}>
                  +45 Object ID
                </span>
              </div>
            </div>

            <button 
              className="btn-new-investigation"
              style={{ marginTop: '14px', width: '100%' }}
              onClick={() => onOpenModal && onOpenModal(currentInc.incident_id)}
            >
              <Eye size={14} /> Open Full Evidence Capsule
            </button>
          </div>
        </div>

        {/* Right Column: Live CCTV Video Feed Player & Track Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Video Player Box with Detected Cheating Bounding Boxes */}
          <div style={{
            background: '#04070d',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            position: 'relative',
            overflow: 'hidden',
            height: '380px',
            display: 'flex',
            alignItems: 'center',
            justify: 'center'
          }}>
            {/* Camera Overlay Badges */}
            <div style={{ position: 'absolute', top: 12, left: 12, display: 'flex', gap: '10px', alignItems: 'center', zIndex: 10, fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
              <span style={{ background: 'rgba(0,0,0,0.75)', color: 'var(--accent-cyan)', padding: '4px 8px', borderRadius: '4px', border: '1px solid var(--border-cyan)' }}>
                CAM_B4_SEC_1
              </span>
              <span style={{ color: 'var(--text-muted)' }}>T+ 09:44:12:08</span>
              <span style={{ color: 'var(--status-critical)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                ● LIVE FEED
              </span>
            </div>

            {/* Video Controls Overlay */}
            <div style={{ position: 'absolute', bottom: 12, right: 12, zIndex: 10, display: 'flex', gap: '8px' }}>
              <button onClick={togglePlay} className="topbar-icon-btn" style={{ background: 'rgba(0,0,0,0.7)', color: '#fff' }}>
                {isPlaying ? <Film size={16} /> : <Play size={16} />}
              </button>
              <button onClick={toggleMute} className="topbar-icon-btn" style={{ background: 'rgba(0,0,0,0.7)', color: '#fff' }}>
                {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </button>
            </div>

            {/* Video Player Stream */}
            <video 
              ref={videoRef}
              src={clipUrl}
              autoPlay
              loop
              muted={isMuted}
              playsInline
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            >
              <source src={clipUrl} type="video/mp4" />
            </video>
          </div>

          {/* Video Track Timeline Bar */}
          <div className="card" style={{ padding: '12px 16px' }}>
            <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
              <span>TIMELINE TRACK</span>
              <span style={{ color: 'var(--accent-cyan)' }}>00:00:00 → 00:00:08.75</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ width: '80px', color: 'var(--text-muted)' }}>Global</span>
                <div style={{ flex: 1, height: '14px', background: '#0a101d', borderRadius: '3px', position: 'relative', overflow: 'hidden', cursor: 'pointer' }} onClick={() => seekToTime(4.0)}>
                  <div style={{ position: 'absolute', left: '40%', width: '35%', height: '100%', background: 'rgba(255, 138, 0, 0.4)' }}></div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ width: '80px', color: 'var(--status-high)' }}>Desk S5</span>
                <div style={{ flex: 1, height: '14px', background: '#0a101d', borderRadius: '3px', position: 'relative', overflow: 'hidden', cursor: 'pointer' }} onClick={() => seekToTime(1.5)}>
                  <div style={{ position: 'absolute', left: '42%', width: '25%', height: '100%', background: 'rgba(255, 138, 0, 0.6)' }}></div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ width: '80px', color: 'var(--status-critical)' }}>Desk S9</span>
                <div style={{ flex: 1, height: '14px', background: '#0a101d', borderRadius: '3px', position: 'relative', overflow: 'hidden', cursor: 'pointer' }} onClick={() => seekToTime(5.0)}>
                  <div style={{ position: 'absolute', left: '45%', width: '20%', height: '100%', background: 'var(--status-critical)' }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Keyframe Thumbnails Strip */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            <div 
              style={{ background: '#080d17', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', textAlign: 'center', cursor: 'pointer' }}
              onClick={() => seekToTime(1.0)}
            >
              <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '4px' }}>T-02s (Pre)</div>
              <div style={{ height: '70px', background: '#04070d', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
                Nominal Posture
              </div>
            </div>

            <div 
              style={{ background: '#080d17', border: '1px solid var(--status-critical)', borderRadius: '6px', padding: '10px', textAlign: 'center', cursor: 'pointer', boxShadow: '0 0 12px rgba(255, 59, 92, 0.25)' }}
              onClick={() => seekToTime(5.0)}
            >
              <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--status-critical)', fontWeight: '700', marginBottom: '4px' }}>T-00s (Peak)</div>
              <div style={{ height: '70px', background: 'rgba(255, 59, 92, 0.15)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: 'var(--status-critical)', fontWeight: '700' }}>
                Phone Extraction
              </div>
            </div>

            <div 
              style={{ background: '#080d17', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '10px', textAlign: 'center', cursor: 'pointer' }}
              onClick={() => seekToTime(8.0)}
            >
              <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '4px' }}>T+03s (Post)</div>
              <div style={{ height: '70px', background: '#04070d', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
                Return to Baseline
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
