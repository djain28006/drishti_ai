import React from 'react';
import { 
  FolderCheck, 
  Layers, 
  Network, 
  Video, 
  Globe, 
  FileText, 
  Plus, 
  Activity, 
  LogOut,
  Shield
} from 'lucide-react';

export default function Sidebar({ currentPage, setCurrentPage, highRiskCount = 0 }) {
  const navItems = [
    { id: 'artifacts', label: 'Artifacts', icon: Layers },
    { id: 'forensics', label: 'Video Forensics', icon: Video, badge: highRiskCount > 0 ? highRiskCount : null },
    { id: 'spatial', label: 'Spatial', icon: Globe },
    { id: 'audit', label: 'Audit Logs', icon: FileText }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo-icon">
          <Shield size={22} />
        </div>
        <div>
          <div className="sidebar-brand-title">Task Force <span>Alpha</span></div>
          <div className="sidebar-brand-sub">Active Ops</div>
        </div>
      </div>

      <div className="sidebar-action-container">
        <button 
          className="btn-new-investigation"
          onClick={() => setCurrentPage('upload')}
        >
          <Plus size={16} /> New Investigation
        </button>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <a
              key={item.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setCurrentPage(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              {item.badge && <span className="badge-count">{item.badge}</span>}
            </a>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="sidebar-footer-item" onClick={() => setCurrentPage('metadata')}>
          <Activity size={16} />
          <span>System Health</span>
        </button>
        <button className="sidebar-footer-item" onClick={() => setCurrentPage('artifacts')}>
          <LogOut size={16} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
