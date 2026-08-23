import React from 'react';
import { Files, Box, Cpu, GitFork, ExternalLink, AlertTriangle } from 'lucide-react';

export const RepositorySummary = ({ repository, summary, failedFiles = [] }) => {
  if (!summary) return null;

  const statCards = [
    {
      title: 'Total Files',
      value: summary.total_files,
      icon: Files,
      color: '#3b82f6',
      bgColor: 'rgba(59, 130, 246, 0.12)',
    },
    {
      title: 'Classes',
      value: summary.total_classes,
      icon: Box,
      color: '#8b5cf6',
      bgColor: 'rgba(139, 92, 246, 0.12)',
    },
    {
      title: 'Functions',
      value: summary.total_functions,
      icon: Cpu,
      color: '#10b981',
      bgColor: 'rgba(16, 185, 129, 0.12)',
    },
    {
      title: 'Dependencies',
      value: summary.total_dependencies,
      icon: GitFork,
      color: '#f59e0b',
      bgColor: 'rgba(245, 158, 11, 0.12)',
    },
  ];

  return (
    <div style={{ margin: '1rem 1rem 1.5rem 1rem' }} className="animate-fade-in">
      {/* Repository Meta Header */}
      {repository && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <span style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)', fontWeight: 600 }}>
              Analyzed Repository
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 700 }}>{repository.name}</h3>
              <a
                href={repository.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'var(--accent-primary)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem' }}
              >
                <span>GitHub</span>
                <ExternalLink size={14} />
              </a>
            </div>
          </div>

          {failedFiles.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.4rem 0.8rem', borderRadius: '8px', backgroundColor: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#fbbf24', fontSize: '0.82rem' }}>
              <AlertTriangle size={15} />
              <span>{failedFiles.length} file(s) skipped due to parsing errors</span>
            </div>
          )}
        </div>
      )}

      {/* Metrics Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="glass-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                backgroundColor: card.bgColor,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: card.color,
                flexShrink: 0
              }}>
                <Icon size={24} />
              </div>
              <div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                  {card.title}
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                  {card.value}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
