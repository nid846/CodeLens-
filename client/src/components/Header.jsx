import React from 'react';
import { Network, GitBranch, Code2 } from 'lucide-react';

export const Header = ({ isBackendOnline }) => {
  return (
    <header className="glass-panel" style={{ margin: '1rem', padding: '1rem 1.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 15px rgba(59, 130, 246, 0.4)'
        }}>
          <Network size={24} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.45rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }} className="gradient-text">
            CodeLens
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
            GitHub Repository Analysis & Dependency Graph
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', padding: '0.4rem 0.85rem', borderRadius: '20px', backgroundColor: 'rgba(255, 255, 255, 0.04)', border: '1px solid var(--border-color)' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isBackendOnline ? 'var(--accent-emerald)' : 'var(--accent-rose)',
            boxShadow: isBackendOnline ? '0 0 8px var(--accent-emerald)' : '0 0 8px var(--accent-rose)'
          }} />
          <span style={{ color: isBackendOnline ? 'var(--text-main)' : 'var(--text-muted)' }}>
            API {isBackendOnline ? 'Connected' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  );
};
