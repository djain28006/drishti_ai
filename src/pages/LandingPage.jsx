import React, { useState, useRef } from 'react';
import { Shield, Play, Pause, Volume2, VolumeX, ArrowRight, Eye, Cpu, FileText, Layers, Lock, Award, CheckCircle, Zap, Activity } from 'lucide-react';

export default function LandingPage({ onProceedToLogin }) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(true);
  const [videoLoaded, setVideoLoaded] = useState(false);

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
    <div className="landing-page-container">
      {/* Top Header Navbar */}
      <header className="landing-header">
        <div className="landing-brand">
          <div className="landing-logo">
            <Shield className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="landing-title">DRISHTI AI</h1>
            <span className="landing-subtitle">FORENSIC EXAMINATION PLATFORM</span>
          </div>
        </div>

        <nav className="landing-nav">
          <a href="#video-showcase">Video Demo</a>
          <a href="#features">Key Features</a>
          <a href="#architecture">Architecture</a>
          <button className="landing-login-btn" onClick={onProceedToLogin}>
            <Lock size={15} />
            <span>Login to Console</span>
          </button>
        </nav>
      </header>

      {/* Main Hero Section */}
      <section className="landing-hero">
        <div className="hero-badge">
          <Zap size={14} />
          <span>OFFLINE CCTV VIDEO SEGMENTATION & ANOMALY DETECTION</span>
        </div>

        <h1 className="hero-headline">
          Autonomous AI-Powered <br />
          <span className="hero-gradient-text">Examination Video Forensics</span>
        </h1>

        <p className="hero-description">
          Convert hours of examination CCTV footage into ranked, explainable, cross-camera evidence capsules. 
          Driven by physical seating maps, motion-gated YOLOv8 detection, and adaptive behavioral baselines.
        </p>

        <div className="hero-cta-group">
          <button className="hero-primary-btn" onClick={onProceedToLogin}>
            <span>Access Forensic Console</span>
            <ArrowRight size={18} />
          </button>
          <a href="#video-showcase" className="hero-secondary-btn">
            <Play size={16} />
            <span>Watch Live Demonstration</span>
          </a>
        </div>
      </section>

      {/* Video Showcase Section */}
      <section id="video-showcase" className="video-showcase-section">
        <div className="section-header">
          <div className="badge-tag">LIVE DEMONSTRATION</div>
          <h2>Examination Surveillance Analysis Showcase</h2>
          <p>Real-time motion estimation, spatial desk grid calibration, and anomalous activity detection.</p>
        </div>

        <div className="video-player-card">
          <div className="video-status-bar">
            <div className="status-indicator">
              <span className="pulse-dot"></span>
              <span>FORENSIC PIPELINE: ACTIVE STREAM</span>
            </div>
            <div className="video-meta-tags">
              <span className="meta-pill">YOLOv8 Custom Trained</span>
              <span className="meta-pill">14 Spatial Desks Calibrated</span>
              <span className="meta-pill">30 FPS Ingestion</span>
            </div>
          </div>

          <div className="video-container">
            <video
              ref={videoRef}
              src="/landing_video.mp4"
              autoPlay
              loop
              muted={isMuted}
              playsInline
              onLoadedData={() => setVideoLoaded(true)}
              className="main-landing-video"
            />
            
            {!videoLoaded && (
              <div className="video-loader-overlay">
                <Activity className="animate-spin text-cyan-400" size={36} />
                <span>Loading Video Stream...</span>
              </div>
            )}

            <div className="video-overlay-controls">
              <button className="video-ctrl-btn" onClick={togglePlay} title={isPlaying ? "Pause" : "Play"}>
                {isPlaying ? <Pause size={18} /> : <Play size={18} />}
              </button>
              <button className="video-ctrl-btn" onClick={toggleMute} title={isMuted ? "Unmute" : "Mute"}>
                {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
              </button>
              <div className="video-tagline">
                <Eye size={16} className="text-cyan-400" />
                <span>CCTV Examination Room Surveillance Feed — Stage 1.5 Calibration Overlay</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid Section */}
      <section id="features" className="landing-features-section">
        <div className="section-header">
          <div className="badge-tag">PLATFORM CAPABILITIES</div>
          <h2>Engineered for Uncompromising Accuracy</h2>
          <p>Strictly investigation-support tool empowering disciplinary committees with verifiable evidence.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon bg-cyan">
              <Cpu size={24} />
            </div>
            <h3>Adaptive Behavior Baseline</h3>
            <p>Learns normal desk posture during calibration and flags sustained deviations using adaptive Z-scores.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon bg-blue">
              <Layers size={24} />
            </div>
            <h3>Multi-Pass Zone Calibration</h3>
            <p>Maps physical exam desk polygons and physical seating locations automatically from surveillance feeds.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon bg-purple">
              <Eye size={24} />
            </div>
            <h3>YOLOv8 Custom Object Model</h3>
            <p>Detects prohibited items including mobile phones, chits, unauthorized desk peekings, and hand gestures.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon bg-red">
              <Shield size={24} />
            </div>
            <h3>Cross-Camera Incident Fusion</h3>
            <p>Correlates multi-camera viewpoints into unified incident timelines, eliminating duplicate alerts.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon bg-amber">
              <FileText size={24} />
            </div>
            <h3>Forensic Evidence Capsules</h3>
            <p>Generates self-contained evidence capsules with pre/during/post event snapshots and formal PDF exports.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon bg-green">
              <Award size={24} />
            </div>
            <h3>Explainable Risk Scoring</h3>
            <p>Provides transparent 0-100 mathematical factor breakdown for every flagged event.</p>
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="landing-cta-banner">
        <div className="cta-content">
          <h2>Ready to Begin Forensic Review?</h2>
          <p>Access the Drishti AI Forensic Console dashboard to manage incidents, search video logs, and export evidence.</p>
          <button className="hero-primary-btn" onClick={onProceedToLogin}>
            <span>Sign In to Forensic Console</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-left">
          <Shield size={18} className="text-cyan-400" />
          <span>DRISHTI AI — Hackathon Solution for Examination CCTV Video Forensics</span>
        </div>
        <div className="footer-right">
          <span>Version 1.0.0</span>
          <span>•</span>
          <span>FastAPI + Vite React</span>
        </div>
      </footer>
    </div>
  );
}
