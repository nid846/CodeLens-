import React, { useState, useEffect } from 'react';
import { Header } from '../components/Header';
import { RepositoryInput } from '../components/RepositoryInput';
import { RepositorySummary } from '../components/RepositorySummary';
import { DependencyGraph } from '../components/DependencyGraph';
import { FileExplorer } from '../components/FileExplorer';
import { CodeSearch } from '../components/CodeSearch';
import { analyzeRepository, checkHealth } from '../services/api';
import { Network, FolderTree, Search } from 'lucide-react';

export const Dashboard = () => {
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [activeTab, setActiveTab] = useState('search'); // 'search' | 'graph' | 'files'

  useEffect(() => {
    const verifyBackend = async () => {
      const res = await checkHealth();
      setIsBackendOnline(res.status === 'ok');
    };
    verifyBackend();
    const interval = setInterval(verifyBackend, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (githubUrl) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await analyzeRepository(githubUrl);
      setAnalysisResult(data);
      setActiveTab('search');
    } catch (err) {
      setError(err.message || 'Failed to analyze repository.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFileNode = (filePath) => {
    setActiveTab('graph');
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', paddingBottom: '3rem' }}>
      <Header isBackendOnline={isBackendOnline} />

      <main>
        {/* Repository Input Section */}
        <RepositoryInput
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          error={error}
        />

        {/* Dashboard Results Section */}
        {analysisResult && (
          <div className="animate-fade-in">
            <RepositorySummary
              repository={analysisResult.repository}
              summary={analysisResult.summary}
              failedFiles={analysisResult.failed_files}
            />

            {/* View Switcher Tabs */}
            <div style={{ margin: '0 1rem 1rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => setActiveTab('search')}
                style={{
                  padding: '0.65rem 1.25rem',
                  borderRadius: '10px',
                  backgroundColor: activeTab === 'search' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(18, 26, 43, 0.6)',
                  border: activeTab === 'search' ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                  color: activeTab === 'search' ? '#ffffff' : 'var(--text-muted)',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}
              >
                <Search size={18} color={activeTab === 'search' ? '#60a5fa' : 'var(--text-dim)'} />
                <span>Semantic & Keyword Search</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('graph')}
                style={{
                  padding: '0.65rem 1.25rem',
                  borderRadius: '10px',
                  backgroundColor: activeTab === 'graph' ? 'rgba(168, 85, 247, 0.2)' : 'rgba(18, 26, 43, 0.6)',
                  border: activeTab === 'graph' ? '1px solid var(--accent-purple)' : '1px solid var(--border-color)',
                  color: activeTab === 'graph' ? '#ffffff' : 'var(--text-muted)',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}
              >
                <Network size={18} color={activeTab === 'graph' ? '#c084fc' : 'var(--text-dim)'} />
                <span>Dependency Graph View</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('files')}
                style={{
                  padding: '0.65rem 1.25rem',
                  borderRadius: '10px',
                  backgroundColor: activeTab === 'files' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(18, 26, 43, 0.6)',
                  border: activeTab === 'files' ? '1px solid #10b981' : '1px solid var(--border-color)',
                  color: activeTab === 'files' ? '#ffffff' : 'var(--text-muted)',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}
              >
                <FolderTree size={18} color={activeTab === 'files' ? '#34d399' : 'var(--text-dim)'} />
                <span>File Explorer & AST Details</span>
              </button>
            </div>

            {/* Tab Views */}
            <div style={{ margin: '0 1rem' }}>
              {activeTab === 'search' && (
                <CodeSearch
                  repositoryId={analysisResult.repository.url}
                  onSelectChunk={(chunk) => setActiveTab('files')}
                />
              )}
              {activeTab === 'graph' && (
                <DependencyGraph
                  graphData={analysisResult.graph}
                  onSelectFile={handleSelectFileNode}
                />
              )}
              {activeTab === 'files' && (
                <FileExplorer
                  files={analysisResult.files}
                  classes={analysisResult.classes}
                  functions={analysisResult.functions}
                  dependencies={analysisResult.dependencies}
                  onSelectFileNode={handleSelectFileNode}
                />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
