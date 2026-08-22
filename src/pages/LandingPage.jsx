import React from 'react';
import { Shield, ArrowRight, Lock, Cpu, Eye, Layers, FileText, Award } from 'lucide-react';
import landingVideo from '../assets/landing_video.mp4';

export default function LandingPage({ onProceedToLogin }) {
  return (
    <div style={{
      width: '100vw',
      minHeight: '100vh',
      backgroundColor: '#070a10',
      color: '#e2e8f0',
      position: 'relative',
      fontFamily: "'Inter', sans-serif",
      overflowY: 'auto',
      overflowX: 'hidden'
    }}>
      {/* Full-Bleed Video Background */}
      <video
        src={landingVideo}
        autoPlay
        loop
        muted
        playsInline
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          objectFit: 'cover',
          zIndex: 0,
          pointerEvents: 'none',
          filter: 'brightness(0.65) contrast(1.1)'
        }}
      />

      {/* Dark Ambient Overlay */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        background: 'radial-gradient(circle at center, rgba(7, 10, 16, 0.45) 0%, rgba(7, 10, 16, 0.88) 100%)',
        zIndex: 1,
        pointerEvents: 'none'
      }} />

      {/* Foreground Content Container */}
      <div style={{ position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {/* Header Navigation */}
        <header style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 48px',
          background: 'rgba(7, 10, 16, 0.65)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(0, 242, 255, 0.15)',
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
              border: '1px solid rgba(0, 242, 255, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#00f2ff',
              boxShadow: '0 0 20px rgba(0, 242, 255, 0.25)'
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
              boxShadow: '0 0 25px rgba(0, 242, 255, 0.35)',
              transition: 'all 0.2s ease'
            }}
          >
            <Lock size={15} />
            <span>Login / Sign In</span>
          </button>
        </header>

        {/* Hero Section */}
        <section style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '80px 24px 60px 24px',
          maxWidth: '1000px',
          margin: '0 auto'
        }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 18px',
            borderRadius: '20px',
            background: 'rgba(0, 242, 255, 0.1)',
            border: '1px solid rgba(0, 242, 255, 0.4)',
            color: '#00f2ff',
            fontSize: '11px',
            fontWeight: '700',
            letterSpacing: '1px',
            marginBottom: '24px',
            backdropFilter: 'blur(8px)'
          }}>
            ⚡ AUTONOMOUS CCTV ANOMALY DETECTION ENGINE
          </div>

          <h1 style={{
            fontSize: '52px',
            fontWeight: '900',
            color: '#ffffff',
            lineHeight: '1.15',
            marginBottom: '20px',
            textShadow: '0 4px 25px rgba(0,0,0,0.9)'
          }}>
            AI-Powered Examination <br />
            <span style={{
              background: 'linear-gradient(135deg, #00f2ff, #2979ff)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Video Forensics Platform
            </span>
          </h1>

          <p style={{
            fontSize: '16px',
            color: '#cbd5e1',
            maxWidth: '720px',
            lineHeight: '1.6',
            marginBottom: '40px',
            textShadow: '0 2px 15px rgba(0,0,0,0.9)'
          }}>
            Offline video segmentation, adaptive baseline anomaly detection, cross-camera incident fusion, and evidence capsule generation.
          </p>

          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <button
              onClick={onProceedToLogin}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                background: 'linear-gradient(135deg, #00f2ff, #0077ff)',
                color: '#030812',
                border: 'none',
                padding: '16px 42px',
                borderRadius: '10px',
                fontWeight: '800',
                fontSize: '16px',
                cursor: 'pointer',
                boxShadow: '0 0 40px rgba(0, 242, 255, 0.5)',
                transition: 'all 0.2s ease'
              }}
            >
              <span>Enter Drishti AI Console</span>
              <ArrowRight size={20} />
            </button>
          </div>
        </section>

        {/* Feature Cards Grid (Scrollable Section) */}
        <section style={{
          padding: '60px 48px',
          maxWidth: '1200px',
          margin: '0 auto',
          width: '100%'
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px'
          }}>
            <div style={{
              background: 'rgba(16, 23, 38, 0.75)',
              border: '1px solid rgba(0, 242, 255, 0.2)',
              borderRadius: '12px',
              padding: '24px',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{ color: '#00f2ff', marginBottom: '14px' }}>
                <Cpu size={28} />
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '8px' }}>
                Adaptive Behavior Baseline
              </h3>
              <p style={{ fontSize: '13px', color: '#8492a6', lineHeight: '1.5', margin: 0 }}>
                Learns normal desk posture during calibration and flags sustained deviations using adaptive Z-scores.
              </p>
            </div>

            <div style={{
              background: 'rgba(16, 23, 38, 0.75)',
              border: '1px solid rgba(0, 242, 255, 0.2)',
              borderRadius: '12px',
              padding: '24px',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{ color: '#4488ff', marginBottom: '14px' }}>
                <Layers size={28} />
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '8px' }}>
                Multi-Pass Zone Calibration
              </h3>
              <p style={{ fontSize: '13px', color: '#8492a6', lineHeight: '1.5', margin: 0 }}>
                Maps physical exam desk polygons and physical seating locations automatically from surveillance feeds.
              </p>
            </div>

            <div style={{
              background: 'rgba(16, 23, 38, 0.75)',
              border: '1px solid rgba(0, 242, 255, 0.2)',
              borderRadius: '12px',
              padding: '24px',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{ color: '#b388ff', marginBottom: '14px' }}>
                <Eye size={28} />
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '8px' }}>
                YOLOv8 Custom Object Model
              </h3>
              <p style={{ fontSize: '13px', color: '#8492a6', lineHeight: '1.5', margin: 0 }}>
                Detects prohibited items including mobile phones, chits, unauthorized desk peekings, and hand gestures.
              </p>
            </div>

            <div style={{
              background: 'rgba(16, 23, 38, 0.75)',
              border: '1px solid rgba(0, 242, 255, 0.2)',
              borderRadius: '12px',
              padding: '24px',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{ color: '#ff8a00', marginBottom: '14px' }}>
                <FileText size={28} />
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fff', marginBottom: '8px' }}>
                Forensic Evidence Capsules
              </h3>
              <p style={{ fontSize: '13px', color: '#8492a6', lineHeight: '1.5', margin: 0 }}>
                Generates self-contained evidence capsules with pre/during/post event snapshots and formal PDF exports.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
