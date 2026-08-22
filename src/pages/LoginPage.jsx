import React, { useState } from 'react';
import { Shield, Mail, Key, AlertCircle, User, ArrowRight, Sparkles } from 'lucide-react';
import { loginWithEmail, registerWithEmail, loginWithGoogle } from '../firebase';

export default function LoginPage({ onLoginSuccess }) {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Senior Forensic Lead');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!email || !email.includes('@')) {
      setErrorMsg('Please enter a valid email address.');
      return;
    }
    if (!password || password.length < 6) {
      setErrorMsg('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);

    try {
      let res;
      if (isRegisterMode) {
        res = await registerWithEmail(email, password, role);
      } else {
        res = await loginWithEmail(email, password, role);
      }

      if (res.success && res.user) {
        onLoginSuccess({
          uid: res.user.uid,
          email: res.user.email || email,
          displayName: res.user.displayName || email.split('@')[0],
          username: res.user.displayName || email.split('@')[0],
          photoURL: res.user.photoURL || null,
          role: role
        });
      } else {
        setErrorMsg(res.error || 'Firebase Authentication failed.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Firebase Auth error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await loginWithGoogle(role);
      if (res.success && res.user) {
        onLoginSuccess({
          uid: res.user.uid,
          email: res.user.email || 'proctor@trinetra.ai',
          displayName: res.user.displayName || 'Forensic Proctor',
          username: res.user.displayName || 'Forensic Proctor',
          photoURL: res.user.photoURL || null,
          role: role
        });
      } else {
        setErrorMsg(res.error || 'Google OAuth failed.');
      }
    } catch (err) {
      setErrorMsg('Google Sign-In failed or popup was closed.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoFill = () => {
    setEmail('proctor@trinetra.ai');
    setPassword('Proctor123!');
  };

  return (
    <div style={{
      width: '100vw',
      minHeight: '100vh',
      backgroundColor: '#070a10',
      color: '#e2e8f0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      fontFamily: "'Inter', -apple-system, sans-serif",
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* CSS Keyframes inline */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Radial Background Glow */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '650px',
        height: '650px',
        background: 'radial-gradient(circle, rgba(0, 242, 255, 0.14) 0%, rgba(41, 121, 255, 0.06) 50%, rgba(0,0,0,0) 70%)',
        pointerEvents: 'none'
      }} />

      <div style={{
        width: '100%',
        maxWidth: '440px',
        backgroundColor: '#101726',
        border: '1px solid rgba(0, 242, 255, 0.4)',
        borderRadius: '16px',
        padding: '36px 32px',
        boxShadow: '0 0 50px rgba(0, 242, 255, 0.2)',
        position: 'relative',
        zIndex: 10,
        animation: 'fadeIn 0.8s ease-in-out'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, rgba(0, 242, 255, 0.25), rgba(41, 121, 255, 0.35))',
            border: '1px solid rgba(0, 242, 255, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto',
            color: '#00f2ff',
            boxShadow: '0 0 25px rgba(0, 242, 255, 0.3)'
          }}>
            <Shield size={32} />
          </div>

          <h2 style={{ fontSize: '22px', fontWeight: '800', color: '#fff', margin: '0 0 6px 0', letterSpacing: '0.5px' }}>
            TRINETRA DRISHTI AI
          </h2>
          <p style={{ fontSize: '13px', color: '#8492a6', margin: 0 }}>
            {isRegisterMode ? 'Register New Forensic Officer' : 'Sign in to Examination Forensic Portal'}
          </p>
        </div>

        {/* Google OAuth Button */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            backgroundColor: '#0b0f19',
            border: '1px solid #24344d',
            color: '#fff',
            padding: '12px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            marginBottom: '16px',
            transition: 'all 0.2s ease'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
            <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.26v3.15C3.25 21.3 7.31 24 12 24z"/>
            <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.26C.46 8.17 0 9.98 0 12s.46 3.83 1.26 5.42l4.02-3.15z"/>
            <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.26 6.58l4.02 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
          </svg>
          <span>Continue with Google OAuth</span>
        </button>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '16px',
          color: '#475569',
          fontSize: '11px'
        }}>
          <div style={{ flex: 1, height: '1px', background: '#172338' }} />
          <span>OR EMAIL AUTHENTICATION</span>
          <div style={{ flex: 1, height: '1px', background: '#172338' }} />
        </div>

        {/* Sign In / Sign Up Mode Switch */}
        <div style={{
          display: 'flex',
          backgroundColor: '#0b0f19',
          padding: '4px',
          borderRadius: '8px',
          marginBottom: '18px'
        }}>
          <button
            type="button"
            onClick={() => setIsRegisterMode(false)}
            style={{
              flex: 1,
              padding: '8px',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '700',
              cursor: 'pointer',
              backgroundColor: !isRegisterMode ? 'rgba(0, 242, 255, 0.15)' : 'transparent',
              color: !isRegisterMode ? '#00f2ff' : '#8492a6'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setIsRegisterMode(true)}
            style={{
              flex: 1,
              padding: '8px',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '700',
              cursor: 'pointer',
              backgroundColor: isRegisterMode ? 'rgba(0, 242, 255, 0.15)' : 'transparent',
              color: isRegisterMode ? '#00f2ff' : '#8492a6'
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error Feedback */}
        {errorMsg && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'rgba(255, 59, 92, 0.15)',
            border: '1px solid rgba(255, 59, 92, 0.4)',
            color: '#ff3b5c',
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '12px',
            marginBottom: '16px'
          }}>
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: '#8492a6', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Mail size={14} />
              <span>Email Address</span>
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="officer@trinetra.ai"
              style={{
                backgroundColor: '#0b0f19',
                border: '1px solid #172338',
                borderRadius: '8px',
                padding: '12px 14px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: '#8492a6', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Key size={14} />
              <span>Firebase Password</span>
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{
                backgroundColor: '#0b0f19',
                border: '1px solid #172338',
                borderRadius: '8px',
                padding: '12px 14px',
                color: '#fff',
                fontSize: '14px',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: '#8492a6', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Shield size={14} />
              <span>Officer Role</span>
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              style={{
                backgroundColor: '#0b0f19',
                border: '1px solid #172338',
                borderRadius: '8px',
                padding: '12px 14px',
                color: '#fff',
                fontSize: '13px',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="Senior Forensic Lead">Senior Forensic Lead</option>
              <option value="Proctor Chief">Examination Chief Proctor</option>
              <option value="Disciplinary Committee">Disciplinary Committee Member</option>
              <option value="Auditor">Security & Audit Observer</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              background: 'linear-gradient(135deg, #00f2ff, #0077ff)',
              color: '#030812',
              border: 'none',
              padding: '14px',
              borderRadius: '8px',
              fontWeight: '700',
              fontSize: '14px',
              cursor: 'pointer',
              marginTop: '4px',
              boxShadow: '0 0 25px rgba(0, 242, 255, 0.35)'
            }}
          >
            {loading ? 'Authenticating with Firebase...' : (isRegisterMode ? 'Create Firebase Account' : 'Sign In to Console')}
            <ArrowRight size={18} />
          </button>

          <button
            type="button"
            onClick={handleQuickDemoFill}
            style={{
              background: 'none',
              border: 'none',
              color: '#00f2ff',
              fontSize: '11px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
              marginTop: '4px'
            }}
          >
            <Sparkles size={12} />
            <span>Pre-fill Demo Credentials (proctor@trinetra.ai)</span>
          </button>
        </form>
      </div>
    </div>
  );
}
