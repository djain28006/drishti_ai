import React, { useState } from 'react';
import { Shield, Lock, User, Key, ArrowRight, CheckCircle2, ChevronRight, ArrowLeft } from 'lucide-react';

export default function LoginPage({ onLoginSuccess, onBackToLanding }) {
  const [username, setUsername] = useState('proctor_admin');
  const [password, setPassword] = useState('••••••••••••');
  const [role, setRole] = useState('Forensic Lead');
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      onLoginSuccess({ username, role });
    }, 600);
  };

  return (
    <div className="login-page-container">
      <div className="login-background-glow"></div>

      <div className="login-top-bar">
        <button className="back-to-landing-btn" onClick={onBackToLanding}>
          <ArrowLeft size={16} />
          <span>Back to Overview</span>
        </button>
      </div>

      <div className="login-card-wrapper">
        <div className="login-card">
          <div className="login-card-header">
            <div className="login-shield-badge">
              <Shield size={32} className="text-cyan-400" />
            </div>
            <h2 className="login-title">DRISHTI AI CONSOLE</h2>
            <p className="login-subtitle">Enter your credentials to access the Forensic Portal</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="username">
                <User size={14} />
                <span>Officer Username / ID</span>
              </label>
              <div className="input-wrapper">
                <input
                  id="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="password">
                <Key size={14} />
                <span>Access Key / Password</span>
              </label>
              <div className="input-wrapper">
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="role">
                <Shield size={14} />
                <span>Forensic Officer Role</span>
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="role-select-input"
              >
                <option value="Forensic Lead">Senior Forensic Lead</option>
                <option value="Proctor Chief">Examination Chief Proctor</option>
                <option value="Disciplinary Committee">Disciplinary Committee Member</option>
                <option value="Auditor">Security & Audit Observer</option>
              </select>
            </div>

            <div className="form-row-checkbox">
              <label className="checkbox-container">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span className="checkmark"></span>
                <span>Keep session active on this workstation</span>
              </label>
            </div>

            <button type="submit" className="login-submit-btn" disabled={isSubmitting}>
              {isSubmitting ? (
                <span>Authenticating Session...</span>
              ) : (
                <>
                  <span>Authenticate & Enter Console</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="login-footer-info">
            <div className="demo-credentials-box">
              <CheckCircle2 size={14} className="text-cyan-400" />
              <span>Demo Mode Active: Pre-authenticated for proctor review</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
