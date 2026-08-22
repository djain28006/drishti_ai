import React, { useState, useRef } from 'react';
import { Shield, Play, Pause, Volume2, VolumeX, ArrowRight, Lock, Activity, Eye, Zap } from 'lucide-react';
import landingVideo from '../assets/landing_video.mp4';

export default function LandingPage({ onProceedToLogin }) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);

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
    <div style={{
      width: '100vw',
      minHeight: '100vh',
      backgroundColor: '#070a10',
      color: '#e2e8f0',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: "'Inter', sans-serif",
      overflowX: 'hidden'
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 40px',
        backgroundColor: 'rgba(11, 15, 25, 0.95)',
        borderBottom: '1px solid #172338',
        position: 'sticky',
        top: 0,
        zIndex: 100
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, rgba(0, 242, 255, 0.25), rgba(41, 121, 255, 0.3))',
            border: '1px solid rgba(0, 242, 255, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#00f2ff'
          }}>
            <Shield size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: '800', color: '#fff', margin: 0, letterSpacing: '0.5px' }}>
              DRISHTI AI
            </h1>
            <span style={{ fontSize: '10px', fontWeight: '700', color: '#00f2ff', letterSpacing: '1px' }}>
              AI EXAMINATION FORENSICS PLATFORM
            </span>
          </div>
        </div>

        <button
          onClick={onProceedToLogin}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'linear-gradient(135deg, #00f2ff, #0088ff)',
            color: '#050b14',
            border: 'none',
            padding: '10px 24px',
            borderRadius: '8px',
            fontWeight: '700',
            fontSize: '13px',
            cursor: 'pointer',
            boxShadow: '0 0 20px rgba(0, 242, 255, 0.3)',
            transition: 'all 0.2s ease'
          }}
        >
          <Lock size={15} />
          <span>Login / Sign In</span>
        </button>
      </header>

      {/* Main Video Showcase Hero */}
      <main style={{
        flex: 1,
        maxWidth: '1200px',
        width: '100%',
        margin: '0 auto',
        padding: '40px 24px 60px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        {/* Title Tag */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 16px',
          borderRadius: '20px',
          background: 'rgba(0, 242, 255, 0.08)',
          border: '1px solid rgba(0, 242, 255, 0.4)',
          color: '#00f2ff',
          fontSize: '11px',
          fontWeight: '700',
          letterSpacing: '0.5px',
          marginBottom: '16px'
        }}>
          <Zap size={14} />
          <span>SURVEILLANCE & ANOMALY DETECTION VIDEO SHOWCASE</span>
        </div>

        <h2 style={{
          fontSize: '32px',
          fontWeight: '900',
          color: '#fff',
          textAlign: 'center',
          marginBottom: '10px',
          lineHeight: '1.2'
        }}>
          Examination Hall Video Pipeline Demonstration
        </h2>

        <p style={{
          fontSize: '14px',
          color: '#8492a6',
          textAlign: 'center',
          maxWidth: '650px',
          marginBottom: '28px'
        }}>
          Watch the live CCTV examination video footage analyzed through multi-pass seating calibration, motion gating, and YOLOv8 object detection.
        </p>

        {/* Video Frame Player */}
        <div style={{
          width: '100%',
          maxWidth: '1000px',
          backgroundColor: '#101726',
          border: '1px solid rgba(0, 242, 255, 0.4)',
          borderRadius: '16px',
          overflow: 'hidden',
          boxShadow: '0 0 50px rgba(0, 242, 255, 0.2)'
        }}>
          {/* Status Bar above Video */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 20px',
            backgroundColor: '#0d121f',
            borderBottom: '1px solid #172338'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#00e676', fontSize: '11px', fontWeight: '700' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00e676', boxShadow: '0 0 8px #00e676' }} />
              <span>CCTV VIDEO FEED — ACTIVE STAGE 1.5 CALIBRATION</span>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <span style={{ fontSize: '10px', background: 'rgba(0,242,255,0.1)', border: '1px solid rgba(0,242,255,0.3)', color: '#00f2ff', padding: '3px 8px', borderRadius: '4px' }}>
                Full HD 1080p
              </span>
              <span style={{ fontSize: '10px', background: 'rgba(0,242,255,0.1)', border: '1px solid rgba(0,242,255,0.3)', color: '#00f2ff', padding: '3px 8px', borderRadius: '4px' }}>
                YOLOv8 Active
              </span>
            </div>
          </div>

          {/* Actual Video Element */}
          <div style={{ position: 'relative', width: '100%', aspectRatio: '16 / 9', backgroundColor: '#000' }}>
            <video
              ref={videoRef}
              src={landingVideo}
              autoPlay
              loop
              controls
              playsInline
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={onProceedToLogin}
          style={{
            marginTop: '36px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'linear-gradient(135deg, #00f2ff, #0077ff)',
            color: '#030812',
            border: 'none',
            padding: '16px 40px',
            borderRadius: '10px',
            fontWeight: '800',
            fontSize: '16px',
            cursor: 'pointer',
            boxShadow: '0 0 35px rgba(0, 242, 255, 0.45)',
            transition: 'all 0.2s ease'
          }}
        >
          <span>Proceed to Firebase Login & Console</span>
          <ArrowRight size={20} />
        </button>
      </main>
    </div>
  );
}
