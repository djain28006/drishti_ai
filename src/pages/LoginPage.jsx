import React, { useState } from 'react';
import { Shield, Lock, Mail, Key, ArrowRight, CheckCircle2, AlertCircle, ArrowLeft, LogIn } from 'lucide-react';
import { loginWithFirebase, registerWithFirebase, loginWithGoogle } from '../firebase';

export default function LoginPage({ onLoginSuccess, onBackToLanding }) {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [email, setEmail] = useState('proctor@drishti.ai');
  const [password, setPassword] = useState('Proctor123!');
  const [role, setRole] = useState('Senior Forensic Lead');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    
    // Firebase constraints validation
    if (!email || !email.includes('@')) {
      setErrorMsg('Please enter a valid institutional email address.');
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
        res = await registerWithFirebase(email, password);
      } else {
        res = await loginWithFirebase(email, password);
      }

      if (res.success) {
        onLoginSuccess({
          email: res.user?.email || email,
          username: email.split('@')[0],
          role: role
        });
      } else {
        setErrorMsg(res.error || 'Authentication failed. Please check credentials.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Firebase login error.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await loginWithGoogle();
      if (res.success) {
        onLoginSuccess({
          email: res.user?.email || 'google.proctor@drishti.ai',
          username: res.user?.displayName || 'Google Proctor',
          role: role
        });
      }
    } catch (err) {
      setErrorMsg('Google authentication cancelled or unavailable.');
    } finally {
      setLoading(false);
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
      position: 'relative'
    }}>
      <div style={{ padding: '24px 40px' }}>
        <button
          onClick={onBackToLanding}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: '#101726',
            border: '1px solid #24344d',
            color: '#8492a6',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '13px',
            cursor: 'pointer'
          }}
        >
          <ArrowLeft size={16} />
          <span>Back to Video Showcase</span>
        </button>
      </div>

      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#101726',
          border: '1px solid rgba(0, 242, 255, 0.4)',
          borderRadius: '16px',
          padding: '36px 32px',
          boxShadow: '0 0 50px rgba(0, 242, 255, 0.2)'
        }}>
          {/* Card Header */}
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, rgba(0, 242, 255, 0.2), rgba(41, 121, 255, 0.3))',
              border: '1px solid rgba(0, 242, 255, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto',
              color: '#00f2ff'
            }}>
              <Shield size={30} />
            </div>

            <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#fff', margin: '0 0 6px 0' }}>
              FIREBASE AUTHENTICATION
            </h2>
            <p style={{ fontSize: '13px', color: '#8492a6', margin: 0 }}>
              {isRegisterMode ? 'Register new forensic officer account' : 'Sign in to Drishti AI Console'}
            </p>
          </div>

          {/* Mode Switch Tabs */}
          <div style={{
            display: 'flex',
            backgroundColor: '#0b0f19',
            padding: '4px',
            borderRadius: '8px',
            marginBottom: '20px'
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

          {/* Error feedback */}
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
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', fontWeight: '600', color: '#8492a6', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Mail size={14} />
                <span>Institutional Email</span>
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@drishti.ai"
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
                placeholder="Min 6 characters"
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
                <span>Assigned Forensic Role</span>
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
                marginTop: '8px',
                boxShadow: '0 0 25px rgba(0, 242, 255, 0.35)'
              }}
            >
              {loading ? 'Authenticating with Firebase...' : (isRegisterMode ? 'Register Officer' : 'Authenticate Session')}
            </button>
          </form>

          {/* Social Sign-In */}
          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <div style={{ fontSize: '11px', color: '#8492a6', marginBottom: '12px' }}>Or connect using Firebase OAuth</div>
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                backgroundColor: '#0b0f19',
                border: '1px solid #24344d',
                color: '#fff',
                padding: '10px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              <span>Sign in with Google</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
