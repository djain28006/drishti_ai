import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import ModalCapsule from './components/ModalCapsule';

import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';

import ArtifactsAnalyticsPage from './pages/ArtifactsAnalyticsPage';
import SpatialPage from './pages/SpatialPage';
import VideoForensicsPage from './pages/VideoForensicsPage';
import AuditLogsPage from './pages/AuditLogsPage';

import DashboardOverviewPage from './pages/DashboardOverviewPage';
import PriorityIncidentsPage from './pages/PriorityIncidentsPage';
import ForensicSearchPage from './pages/ForensicSearchPage';
import DeskDossiersPage from './pages/DeskDossiersPage';
import EvidenceClipsPage from './pages/EvidenceClipsPage';
import PDFReportsPage from './pages/PDFReportsPage';
import IngestVideoPage from './pages/IngestVideoPage';
import ProcessingPage from './pages/ProcessingPage';
import MetadataInfoPage from './pages/MetadataInfoPage';

import './styles/theme.css';

const API_BASE = window.location.origin;

export default function App() {
  const [viewMode, setViewMode] = useState('landing'); // 'landing' | 'login' | 'dashboard'
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState('artifacts');
  const [currentData, setCurrentData] = useState({
    video_name: 'Examination_Surveillance.mp4',
    total_zones: 12,
    detected_zones: 12,
    incidents: []
  });
  const [funnelMetrics, setFunnelMetrics] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeModalIncident, setActiveModalIncident] = useState(null);
  const [jobId, setJobId] = useState(null);

  const loadCurrentAnalysis = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analysis/current`);
      if (res.ok) {
        const data = await res.json();
        setCurrentData(prev => ({ ...prev, ...data }));
      }
    } catch (err) {
      console.warn("Could not fetch current analysis:", err);
    }
  };

  const loadIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/incidents`);
      if (res.ok) {
        const incs = await res.json();
        setCurrentData(prev => ({ ...prev, incidents: incs }));
      }
    } catch (err) {
      console.warn("Could not fetch incidents:", err);
    }
  };

  const loadFunnel = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/demo/funnel`);
      if (res.ok) {
        const funnel = await res.json();
        setFunnelMetrics(funnel);
      }
    } catch (err) {
      console.warn("Could not fetch funnel metrics:", err);
    }
  };

  useEffect(() => {
    loadCurrentAnalysis();
    loadIncidents();
    loadFunnel();
  }, []);

  const openCapsuleModal = async (incidentId) => {
    let inc = (currentData.incidents || []).find(i => String(i.incident_id) === String(incidentId));
    if (!inc) {
      try {
        const res = await fetch(`${API_BASE}/api/incidents/${encodeURIComponent(incidentId)}`);
        if (res.ok) {
          const data = await res.json();
          inc = data.incident || data;
        }
      } catch (err) {
        console.error("Modal fetch error:", err);
      }
    }
    if (!inc) {
      inc = { incident_id: incidentId, risk_level: 'HIGH', risk_score: 80 };
    }
    setActiveModalIncident(inc);
  };

  const highRiskCount = (currentData.incidents || []).filter(
    i => i.risk_level === 'HIGH' || i.risk_level === 'CRITICAL'
  ).length;

  if (viewMode === 'landing') {
    return (
      <LandingPage 
        onProceedToLogin={() => setViewMode('login')} 
      />
    );
  }

  if (viewMode === 'login') {
    return (
      <LoginPage 
        onLoginSuccess={(userData) => {
          setUser(userData);
          setViewMode('dashboard');
        }}
        onBackToLanding={() => setViewMode('landing')}
      />
    );
  }

  return (
    <div className="app-container">
      <Sidebar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage} 
        highRiskCount={highRiskCount}
      />

      <div className="main-wrapper">
        <Topbar 
          currentPage={currentPage} 
          setCurrentPage={setCurrentPage}
          onSearch={(query) => {
            setSearchQuery(query);
            setCurrentPage('search');
          }}
        />

        <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {currentPage === 'artifacts' && (
            <ArtifactsAnalyticsPage />
          )}

          {currentPage === 'spatial' && (
            <SpatialPage onSelectIncident={openCapsuleModal} />
          )}

          {currentPage === 'forensics' && (
            <VideoForensicsPage 
              currentData={currentData} 
              onOpenModal={openCapsuleModal}
            />
          )}

          {currentPage === 'audit' && (
            <AuditLogsPage />
          )}

          {currentPage === 'dashboard' && (
            <DashboardOverviewPage 
              currentData={currentData} 
              funnelMetrics={funnelMetrics}
              onOpenModal={openCapsuleModal}
              setCurrentPage={setCurrentPage}
              apiBase={API_BASE}
            />
          )}

          {currentPage === 'search' && (
            <ForensicSearchPage 
              initialQuery={searchQuery}
              apiBase={API_BASE}
              onOpenModal={openCapsuleModal}
            />
          )}

          {currentPage === 'clips' && (
            <EvidenceClipsPage 
              currentData={currentData}
              onOpenModal={openCapsuleModal}
            />
          )}

          {currentPage === 'reports' && (
            <PDFReportsPage 
              currentData={currentData}
              apiBase={API_BASE}
            />
          )}

          {currentPage === 'upload' && (
            <IngestVideoPage 
              apiBase={API_BASE}
              onStartJob={(id) => setJobId(id)}
              setCurrentPage={setCurrentPage}
            />
          )}

          {currentPage === 'processing' && (
            <ProcessingPage 
              jobId={jobId}
              apiBase={API_BASE}
              onComplete={() => {
                loadCurrentAnalysis();
                loadIncidents();
              }}
              setCurrentPage={setCurrentPage}
            />
          )}

          {currentPage === 'metadata' && (
            <MetadataInfoPage />
          )}
        </main>
      </div>

      {activeModalIncident && (
        <ModalCapsule 
          incident={activeModalIncident} 
          onClose={() => setActiveModalIncident(null)} 
        />
      )}
    </div>
  );
}
