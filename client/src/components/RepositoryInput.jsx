import React, { useState } from 'react';
import { Search, Loader2, GitPullRequest, AlertCircle, ArrowRight, Sparkles } from 'lucide-react';

export const RepositoryInput = ({ onAnalyze, isLoading, error }) => {
  const [url, setUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url.trim()) {
      onAnalyze(url.trim());
    }
  };

  const handlePresetClick = (presetUrl) => {
    setUrl(presetUrl);
    onAnalyze(presetUrl);
  };

  const presets = [
    { name: 'Flask (Python)', url: 'https://github.com/pallets/flask' },
    { name: 'Express (JavaScript)', url: 'https://github.com/expressjs/express' },
    { name: 'Pydantic (Python)', url: 'https://github.com/pydantic/pydantic' },
  ];

  return (
    <div className="glass-panel animate-fade-in" style={{ margin: '1rem', padding: '2rem', textAlign: 'center' }}>
      <div style={{ maxWidth: '750px', margin: '0 auto' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.9rem', borderRadius: '20px', backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.25)', color: '#60a5fa', fontSize: '0.8rem', fontWeight: 600, marginBottom: '1rem' }}>
          <Sparkles size={14} /> AST Static Code Analysis
        </div>

        <h2 style={{ fontSize: '1.85rem', fontWeight: 800, marginBottom: '0.5rem' }}>
          Analyze Any Public GitHub Repository
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '1.75rem' }}>
          Enter a public repository URL to parse AST structure, discover classes, functions, and visualize file-level dependencies.
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <div style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }}>
              <GitPullRequest size={20} />
            </div>
            <input
              type="text"
              placeholder="https://github.com/username/repository"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '0.9rem 1rem 0.9rem 3rem',
                borderRadius: '10px',
                backgroundColor: 'rgba(9, 13, 22, 0.8)',
                border: '1px solid var(--border-color)',
                color: '#ffffff',
                fontSize: '0.95rem',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--accent-primary)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--border-color)')}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            style={{
              padding: '0.9rem 1.75rem',
              borderRadius: '10px',
              background: isLoading || !url.trim() ? '#374151' : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s',
              boxShadow: isLoading || !url.trim() ? 'none' : '0 4px 15px rgba(59, 130, 246, 0.35)',
            }}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                <span>Analyzing AST...</span>
              </>
            ) : (
              <>
                <span>Analyze Repository</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Quick Presets */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Try sample repo:</span>
          {presets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetClick(preset.url)}
              disabled={isLoading}
              style={{
                fontSize: '0.78rem',
                padding: '0.3rem 0.7rem',
                borderRadius: '6px',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-muted)',
                transition: 'all 0.15s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(59, 130, 246, 0.15)';
                e.currentTarget.style.color = '#ffffff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                e.currentTarget.style.color = 'var(--text-muted)';
              }}
            >
              {preset.name}
            </button>
          ))}
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{ marginTop: '1.25rem', padding: '0.85rem 1.25rem', borderRadius: '10px', backgroundColor: 'rgba(244, 63, 94, 0.12)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '0.75rem', textAlign: 'left' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <div style={{ fontSize: '0.88rem' }}>{error}</div>
          </div>
        )}
      </div>
    </div>
  );
};
