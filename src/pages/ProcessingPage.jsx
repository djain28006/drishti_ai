import React, { useEffect, useState } from 'react';
import { Cpu, CheckCircle2, Loader2, Terminal, ArrowRight } from 'lucide-react';

export default function ProcessingPage({ jobId: initialJobId, apiBase = '', onComplete, setCurrentPage }) {
  const [jobId, setJobId] = useState(initialJobId || 'f83e7a5f');
  const [progress, setProgress] = useState(0);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [currentStageLabel, setCurrentStageLabel] = useState('Video Loading');
  const [logs, setLogs] = useState([
    '[INIT] Offline Forensic Engine v2.4 initialized',
    '[INIT] Connecting to MOG2 Motion Estimation CUDA module...',
    '[STG 0] Loading video stream: CCTV_HALL_B4_2026-08-22.mp4'
  ]);
  const [isCompleted, setIsCompleted] = useState(false);

  const stages = [
    'Video Loading',
    'Preprocessing',
    'Zone Calibration',
    'Motion Analysis',
    'Object Detection',
    'Tracking Fusion',
    'Event Segmentation',
    'Activity Analysis',
    'Heatmap Generation',
    'Report Generation'
  ];

  useEffect(() => {
    let interval = null;

    if (initialJobId) {
      // Real backend polling mode
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${apiBase}/api/status/${initialJobId}`);
          if (res.ok) {
            const data = await res.json();
            const pct = data.pct !== undefined ? data.pct : (data.progress || 0);
            setProgress(pct);
            
            if (data.current_stage_label) {
              setCurrentStageLabel(data.current_stage_label);
            }
            if (data.current_stage !== undefined) {
              setCurrentStageIndex(data.current_stage);
            }

            // Fetch logs
            try {
              const logsRes = await fetch(`${apiBase}/api/status/${initialJobId}/logs`);
              if (logsRes.ok) {
                const logsData = await logsRes.json();
                if (logsData.logs && logsData.logs.length > 0) {
                  setLogs(logsData.logs);
                }
              }
            } catch (e) {
              // ignore
            }

            if (data.status === 'completed' || pct >= 100) {
              clearInterval(interval);
              setIsCompleted(true);
              if (onComplete) onComplete();
              setTimeout(() => {
                setCurrentPage('artifacts');
              }, 1200);
            }
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 800);
    } else {
      // Simulated interactive pipeline execution mode
      let currentPct = 0;
      let stageIdx = 0;

      interval = setInterval(() => {
        currentPct += 2;
        if (currentPct > 100) currentPct = 100;

        stageIdx = Math.min(Math.floor((currentPct / 100) * stages.length), stages.length - 1);

        setProgress(currentPct);
        setCurrentStageIndex(stageIdx);
        setCurrentStageLabel(stages[stageIdx]);

        // Append log if new stage entered
        const newLog = `[STG ${stageIdx}] Executing ${stages[stageIdx]}... (${currentPct}%)`;
        setLogs(prev => {
          if (prev[prev.length - 1] !== newLog) {
            return [...prev, newLog];
          }
          return prev;
        });

        if (currentPct >= 100) {
          clearInterval(interval);
          setIsCompleted(true);
          setLogs(prev => [...prev, '[SUCCESS] Pipeline completed successfully. 12 ROI zones calibrated.']);
          if (onComplete) onComplete();
          setTimeout(() => {
            setCurrentPage('artifacts');
          }, 1500);
        }
      }, 150);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [initialJobId, apiBase, onComplete, setCurrentPage]);

  return (
    <div className="content-area" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '82vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: '680px', textAlign: 'center', border: '1px solid var(--border-cyan)', position: 'relative' }}>
        
        {/* Top Pulsing Chip Icon */}
        <div style={{
          display: 'inline-flex',
          padding: '16px',
          background: 'rgba(0, 242, 255, 0.1)',
          borderRadius: '50%',
          marginBottom: '16px',
          color: 'var(--accent-cyan)',
          boxShadow: isCompleted ? '0 0 25px rgba(0, 230, 118, 0.4)' : '0 0 20px rgba(0, 242, 255, 0.3)'
        }}>
          <Cpu size={42} />
        </div>

        <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#fff', marginBottom: '4px' }}>
          {isCompleted ? 'Forensic Pipeline Completed' : 'Running Offline Forensic Pipeline'}
        </h2>

        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '20px', fontFamily: 'var(--font-mono)' }}>
          Job ID: <strong style={{ color: '#fff' }}>{jobId}</strong> | Stage: <strong style={{ color: 'var(--accent-cyan)' }}>{currentStageLabel}</strong>
        </p>

        {/* Progress Bar Container */}
        <div style={{ width: '100%', height: '10px', background: '#0a101d', borderRadius: '5px', overflow: 'hidden', marginBottom: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{
            width: `${progress}%`,
            height: '100%',
            background: isCompleted ? 'linear-gradient(90deg, #00e676, var(--accent-cyan))' : 'linear-gradient(90deg, var(--accent-blue), var(--accent-cyan))',
            transition: 'width 0.2s ease',
            boxShadow: '0 0 10px var(--accent-cyan)'
          }}></div>
        </div>

        {/* Percentage Label */}
        <div style={{ fontSize: '15px', fontFamily: 'var(--font-mono)', fontWeight: '800', color: isCompleted ? 'var(--status-nominal)' : 'var(--accent-cyan)', marginBottom: '24px' }}>
          {progress}% COMPLETED
        </div>

        {/* 10 Stages Checklist Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', textAlign: 'left', fontFamily: 'var(--font-mono)', fontSize: '11px', marginBottom: '20px' }}>
          {stages.map((stg, idx) => {
            const isDone = idx < currentStageIndex || progress >= 100;
            const isCurrent = idx === currentStageIndex && progress < 100;
            return (
              <div 
                key={stg} 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px', 
                  padding: '8px 12px', 
                  background: isCurrent ? 'rgba(0, 242, 255, 0.08)' : '#070b14', 
                  borderRadius: '6px', 
                  border: isCurrent ? '1px solid var(--accent-cyan)' : isDone ? '1px solid rgba(0, 230, 118, 0.3)' : '1px solid var(--border-color)',
                  transition: 'all 0.2s ease'
                }}
              >
                {isDone ? (
                  <CheckCircle2 size={16} style={{ color: 'var(--status-nominal)' }} />
                ) : isCurrent ? (
                  <Loader2 size={16} className="spin" style={{ color: 'var(--accent-cyan)' }} />
                ) : (
                  <div style={{ width: '16px', height: '16px', borderRadius: '50%', border: '1px solid var(--text-dim)' }}></div>
                )}
                <span style={{ color: isDone ? '#fff' : isCurrent ? 'var(--accent-cyan)' : 'var(--text-muted)', fontWeight: isCurrent ? '700' : '500' }}>
                  {stg}
                </span>
              </div>
            );
          })}
        </div>

        {/* Live Terminal Log Streamer */}
        <div style={{
          background: '#04070d',
          border: '1px solid var(--border-color)',
          borderRadius: '6px',
          padding: '12px',
          textAlign: 'left',
          fontFamily: 'var(--font-mono)',
          fontSize: '11px',
          maxHeight: '120px',
          overflowY: 'auto',
          color: 'var(--text-muted)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-cyan)', marginBottom: '6px', borderBottom: '1px solid var(--border-color)', paddingBottom: '4px' }}>
            <Terminal size={12} /> Pipeline Execution Log
          </div>
          {logs.map((lg, i) => (
            <div key={i} style={{ color: lg.includes('SUCCESS') ? 'var(--status-nominal)' : lg.includes('STG') ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
              {lg}
            </div>
          ))}
        </div>

        {isCompleted && (
          <button
            className="btn-new-investigation"
            style={{ marginTop: '16px', width: '100%' }}
            onClick={() => setCurrentPage('artifacts')}
          >
            View Investigation Telemetry & Artifacts <ArrowRight size={14} />
          </button>
        )}

      </div>
    </div>
  );
}
