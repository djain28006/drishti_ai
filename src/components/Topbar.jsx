import React, { useState } from 'react';
import { Search, Bell, Settings, HelpCircle, User, AlertTriangle, LogOut, Shield } from 'lucide-react';

export default function Topbar({ currentPage, setCurrentPage, onSearch, user, onLogout }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      setCurrentPage('search');
      if (onSearch) onSearch(searchQuery);
    }
  };

  const displayName = user?.displayName || user?.username || user?.email?.split('@')[0] || 'Forensic Officer';
  const displayEmail = user?.email || 'officer@trinetra.ai';
  const displayRole = user?.role || 'Senior Forensic Lead';
  const photoURL = user?.photoURL;

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="topbar-brand-title" onClick={() => setCurrentPage('artifacts')} style={{ cursor: 'pointer' }}>
          DRISHTI AI
        </div>
      </div>

      <div className="topbar-search">
        <Search size={14} className="topbar-search-icon" />
        <input 
          type="text" 
          placeholder="Search Telemetry (⌘K)..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>

      <div className="topbar-right" style={{ position: 'relative' }}>
        <div className="session-badge">
          ACTIVE LINK: <strong>Session 0812-B</strong>
        </div>

        {/* Notifications Button & Dropdown */}
        <div style={{ position: 'relative' }}>
          <button 
            className="topbar-icon-btn" 
            title="Notifications"
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowProfile(false);
            }}
          >
            <Bell size={18} />
            <span className="notification-dot"></span>
          </button>

          {showNotifications && (
            <div style={{
              position: 'absolute',
              top: '42px',
              right: '0',
              width: '320px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-cyan)',
              borderRadius: '8px',
              padding: '14px',
              boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
              zIndex: 100
            }}>
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#fff', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Security Notifications</span>
                <span className="badge badge-critical" style={{ fontSize: '9px' }}>2 New Alerts</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                <div style={{ padding: '8px', background: '#0a101d', borderRadius: '4px', borderLeft: '3px solid var(--status-critical)' }}>
                  <div style={{ color: 'var(--status-critical)', fontWeight: '700' }}>
                    <AlertTriangle size={12} style={{ verticalAlign: 'middle' }} /> INC-FB313E Cheating Alert
                  </div>
                  <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>Cell phone detected at Desk S9. Confidence: 98%</div>
                </div>

                <div style={{ padding: '8px', background: '#0a101d', borderRadius: '4px', borderLeft: '3px solid var(--status-high)' }}>
                  <div style={{ color: 'var(--status-high)', fontWeight: '700' }}>
                    <AlertTriangle size={12} style={{ verticalAlign: 'middle' }} /> Gaze Anomaly at Desk S5
                  </div>
                  <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>Prolonged glance right detected (94%)</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Settings Button */}
        <button 
          className="topbar-icon-btn" 
          title="Settings" 
          onClick={() => setCurrentPage('metadata')}
        >
          <Settings size={18} />
        </button>

        {/* Help Button */}
        <button 
          className="topbar-icon-btn" 
          title="Help"
          onClick={() => setCurrentPage('metadata')}
        >
          <HelpCircle size={18} />
        </button>

        {/* User Profile Avatar Section */}
        <div style={{ position: 'relative' }}>
          <div 
            className="user-avatar" 
            title={displayName} 
            style={{ 
              cursor: 'pointer',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: photoURL ? '2px solid var(--accent-cyan)' : '1px solid var(--border-cyan)'
            }}
            onClick={() => {
              setShowProfile(!showProfile);
              setShowNotifications(false);
            }}
          >
            {photoURL ? (
              <img 
                src={photoURL} 
                alt={displayName} 
                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} 
              />
            ) : (
              <User size={18} />
            )}
          </div>

          {/* Profile & Logout Dropdown */}
          {showProfile && (
            <div style={{
              position: 'absolute',
              top: '46px',
              right: '0',
              width: '260px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-cyan)',
              borderRadius: '12px',
              padding: '16px',
              boxShadow: '0 10px 40px rgba(0,242,255,0.2)',
              zIndex: 100
            }}>
              {/* User Avatar & Info */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
                <div style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '50%',
                  overflow: 'hidden',
                  background: 'rgba(0, 242, 255, 0.15)',
                  border: '1px solid var(--border-cyan)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-cyan)'
                }}>
                  {photoURL ? (
                    <img src={photoURL} alt={displayName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <User size={22} />
                  )}
                </div>
                <div style={{ overflow: 'hidden' }}>
                  <div style={{ fontSize: '13px', fontWeight: '800', color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {displayName}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {displayEmail}
                  </div>
                </div>
              </div>

              <div style={{ 
                fontSize: '11px', 
                color: 'var(--accent-cyan)', 
                fontFamily: 'var(--font-mono)', 
                backgroundColor: 'rgba(0, 242, 255, 0.08)',
                padding: '6px 10px',
                borderRadius: '6px',
                marginBottom: '14px',
                border: '1px solid rgba(0, 242, 255, 0.2)'
              }}>
                Role: {displayRole}
              </div>

              {/* Logout Button */}
              {onLogout && (
                <button
                  onClick={() => {
                    setShowProfile(false);
                    onLogout();
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    padding: '10px',
                    background: 'rgba(255, 59, 92, 0.15)',
                    border: '1px solid rgba(255, 59, 92, 0.4)',
                    color: 'var(--status-critical)',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <LogOut size={14} />
                  <span>Log Out to Landing Page</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
