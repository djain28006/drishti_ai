import React, { useState } from 'react';
import { Search, Eye, Filter } from 'lucide-react';

export default function ForensicSearchPage({ initialQuery = '', apiBase = '', onOpenModal }) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/search?q=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || data);
      }
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="content-area">
      <div>
        <h1 className="page-title">Forensic Query & Telemetry Search</h1>
        <p className="page-subtitle">Search natural language behavioral events across all video feeds and desk telemetry.</p>
      </div>

      <form onSubmit={handleSearch} className="card" style={{ display: 'flex', gap: '12px' }}>
        <div className="topbar-search" style={{ flex: 1 }}>
          <Search size={16} className="topbar-search-icon" />
          <input 
            type="text" 
            placeholder="Search keywords e.g. 'glance', 'desk S5', 'phone', 'high risk'..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ width: '100%', fontSize: '13px', padding: '10px 12px 10px 36px' }}
          />
        </div>
        <button type="submit" className="btn-new-investigation" style={{ width: 'auto', padding: '10px 24px' }}>
          {loading ? 'Searching...' : 'Run Query'}
        </button>
      </form>

      {results && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
            Found {results.length} matching item(s) for "{query}":
          </div>

          {results.map((inc) => (
            <div key={inc.incident_id || inc.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                  <span className={`badge ${inc.risk_level === 'CRITICAL' ? 'badge-critical' : inc.risk_level === 'HIGH' ? 'badge-high' : 'badge-med'}`}>{inc.risk_level}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '800', color: '#fff' }}>{inc.incident_id}</span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  📍 {inc.location_desc || 'Desk Area'} | Risk Score: <strong>{inc.risk_score}</strong>
                </div>
              </div>

              <button className="btn-new-investigation" style={{ width: 'auto' }} onClick={() => onOpenModal && onOpenModal(inc.incident_id)}>
                <Eye size={14} /> Inspect Capsule
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
