import React, { useState } from 'react';
import { Search, Sparkles, Terminal, FileCode, CheckCircle2, AlertCircle, Layers, ArrowRight } from 'lucide-react';
import { searchCode } from '../services/api';

export const CodeSearch = ({ repositoryId, onSelectChunk }) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [topK, setTopK] = useState(10);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim() || !repositoryId) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const data = await searchCode(repositoryId, query.trim(), topK);
      setResults(data.results || []);
      setHasSearched(true);
    } catch (err) {
      setSearchError(err.message || 'Error executing search');
    } finally {
      setIsSearching(false);
    }
  };

  const getBadgeStyle = (searchType) => {
    if (searchType === 'hybrid') {
      return {
        bg: 'rgba(168, 85, 247, 0.15)',
        border: '1px solid rgba(168, 85, 247, 0.4)',
        color: '#c084fc',
        label: '⚡ Hybrid (BM25 + Semantic)',
      };
    } else if (searchType === 'semantic') {
      return {
        bg: 'rgba(59, 130, 246, 0.15)',
        border: '1px solid rgba(59, 130, 246, 0.4)',
        color: '#60a5fa',
        label: '🧠 Semantic (Jina / Qdrant)',
      };
    }
    return {
      bg: 'rgba(234, 179, 8, 0.15)',
      border: '1px solid rgba(234, 179, 8, 0.4)',
      color: '#facc15',
      label: '🔍 BM25 Keyword',
    };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Search Input Bar */}
      <div
        style={{
          background: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(12px)',
          border: '1px solid var(--border-color)',
          borderRadius: '16px',
          padding: '1.25rem',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.25)',
        }}
      >
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search
              size={18}
              color="var(--text-dim)"
              style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search code semantics, functions, logic, or keywords (e.g. 'How does authentication work?')..."
              style={{
                width: '100%',
                padding: '0.85rem 1rem 0.85rem 2.8rem',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(10, 15, 29, 0.85)',
                color: '#f8fafc',
                fontSize: '0.95rem',
                outline: 'none',
                transition: 'border 0.2s',
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{
                padding: '0.85rem 0.75rem',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(10, 15, 29, 0.85)',
                color: 'var(--text-muted)',
                fontSize: '0.85rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
            </select>

            <button
              type="submit"
              disabled={isSearching || !query.trim()}
              style={{
                padding: '0.85rem 1.75rem',
                borderRadius: '12px',
                background: isSearching || !query.trim()
                  ? 'rgba(59, 130, 246, 0.3)'
                  : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                border: 'none',
                color: '#ffffff',
                fontWeight: 600,
                fontSize: '0.95rem',
                cursor: isSearching || !query.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: isSearching || !query.trim() ? 'none' : '0 4px 14px rgba(59, 130, 246, 0.4)',
                transition: 'all 0.2s',
              }}
            >
              {isSearching ? (
                <>
                  <Sparkles className="animate-spin" size={18} />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  <span>Search Code</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Quick Suggestion Pills */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Try queries:</span>
          {['authentication login handling', 'database connection or models', 'route handlers and controllers', 'helper utilities'].map((pill) => (
            <button
              key={pill}
              type="button"
              onClick={() => {
                setQuery(pill);
              }}
              style={{
                fontSize: '0.75rem',
                padding: '0.25rem 0.6rem',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              {pill}
            </button>
          ))}
        </div>
      </div>

      {/* Error Alert */}
      {searchError && (
        <div
          style={{
            padding: '1rem',
            borderRadius: '12px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            fontSize: '0.9rem',
          }}
        >
          <AlertCircle size={20} />
          <span>{searchError}</span>
        </div>
      )}

      {/* Results Header */}
      {hasSearched && !isSearching && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 0.5rem' }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Found <strong style={{ color: '#ffffff' }}>{results.length}</strong> matching code chunks for "{query}"
          </div>
        </div>
      )}

      {/* Results List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {results.map((item, idx) => {
          const badge = getBadgeStyle(item.search_type);
          return (
            <div
              key={item.chunk_id || idx}
              style={{
                background: 'rgba(15, 23, 42, 0.65)',
                border: '1px solid var(--border-color)',
                borderRadius: '14px',
                overflow: 'hidden',
                transition: 'border 0.2s, box-shadow 0.2s',
              }}
            >
              {/* Chunk Header */}
              <div
                style={{
                  padding: '0.85rem 1.25rem',
                  background: 'rgba(10, 15, 29, 0.6)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <FileCode size={18} color="#60a5fa" />
                  <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem' }}>
                    {item.file_path}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                    (Lines {item.start_line}–{item.end_line})
                  </span>
                  {item.function_name && (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        background: 'rgba(59, 130, 246, 0.1)',
                        color: '#93c5fd',
                        fontFamily: 'monospace',
                      }}
                    >
                      fn: {item.function_name}
                    </span>
                  )}
                  {item.class_name && (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        background: 'rgba(139, 92, 246, 0.1)',
                        color: '#c4b5fd',
                        fontFamily: 'monospace',
                      }}
                    >
                      class: {item.class_name}
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '20px',
                      background: badge.bg,
                      border: badge.border,
                      color: badge.color,
                      fontWeight: 600,
                    }}
                  >
                    {badge.label}
                  </span>
                  <span
                    style={{
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      color: '#34d399',
                      background: 'rgba(16, 185, 129, 0.1)',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '6px',
                    }}
                  >
                    Score: {(item.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Code Snippet */}
              <div
                style={{
                  padding: '1rem 1.25rem',
                  background: 'rgba(5, 8, 16, 0.7)',
                  fontFamily: 'var(--font-mono, monospace)',
                  fontSize: '0.85rem',
                  lineHeight: '1.5',
                  color: '#e2e8f0',
                  overflowX: 'auto',
                  maxHeight: '320px',
                  overflowY: 'auto',
                }}
              >
                <pre style={{ margin: 0 }}>
                  <code>{item.code}</code>
                </pre>
              </div>
            </div>
          );
        })}

        {hasSearched && results.length === 0 && !isSearching && (
          <div
            style={{
              padding: '3rem',
              textAlign: 'center',
              background: 'rgba(15, 23, 42, 0.4)',
              borderRadius: '16px',
              border: '1px dashed var(--border-color)',
            }}
          >
            <Search size={40} color="var(--text-dim)" style={{ marginBottom: '1rem', opacity: 0.5 }} />
            <h3 style={{ margin: 0, color: 'var(--text-muted)', fontSize: '1.1rem' }}>No matching code chunks found</h3>
            <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              Try broadening your search keywords or phrasing your query differently.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
