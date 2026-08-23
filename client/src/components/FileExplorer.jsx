import React, { useState } from 'react';
import { Search, FileCode, Box, Cpu, ArrowRight, Layers } from 'lucide-react';

export const FileExplorer = ({ files = [], classes = [], functions = [], dependencies = [], onSelectFileNode }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFile, setSelectedFile] = useState(files.length > 0 ? files[0].path : null);

  const filteredFiles = files.filter(f =>
    f.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const activeFileInfo = files.find(f => f.path === selectedFile);
  const activeClasses = classes.filter(c => c.file_path === selectedFile);
  const activeFunctions = functions.filter(fn => fn.file_path === selectedFile);
  const activeDependencies = dependencies.filter(d => d.source_file === selectedFile);
  const activeIncomingDependencies = dependencies.filter(d => d.target_file === selectedFile);

  const getLanguageBadgeColor = (lang) => {
    switch (lang) {
      case 'Python': return { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa' };
      case 'Java': return { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24' };
      case 'JavaScript': return { bg: 'rgba(234, 179, 8, 0.15)', text: '#fde047' };
      case 'TypeScript': return { bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8' };
      case 'EJS': return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399' };
      case 'HTML': return { bg: 'rgba(244, 63, 94, 0.15)', text: '#f87171' };
      case 'CSS': return { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc' };
      default: return { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' };
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'grid', gridTemplateColumns: '320px 1fr', minHeight: '520px', overflow: 'hidden' }}>
      <div style={{ borderRight: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
            <input
              type="text"
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem 0.5rem 2.1rem',
                borderRadius: '6px',
                backgroundColor: 'rgba(9, 13, 22, 0.6)',
                border: '1px solid var(--border-color)',
                color: '#ffffff',
                fontSize: '0.85rem',
              }}
            />
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
          {filteredFiles.map((file) => {
            const isSelected = file.path === selectedFile;
            const langStyle = getLanguageBadgeColor(file.language);

            return (
              <div
                key={file.path}
                onClick={() => setSelectedFile(file.path)}
                style={{
                  padding: '0.65rem 0.75rem',
                  borderRadius: '8px',
                  backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  border: isSelected ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                  marginBottom: '0.25rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                  <span style={{ fontSize: '0.88rem', fontWeight: isSelected ? 600 : 400, color: isSelected ? '#ffffff' : 'var(--text-main)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {file.name}
                  </span>
                  <span style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem', borderRadius: '4px', backgroundColor: langStyle.bg, color: langStyle.text, fontWeight: 600 }}>
                    {file.language}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {file.path}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ padding: '1.5rem', overflowY: 'auto' }}>
        {activeFileInfo ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)', marginBottom: '1.25rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <FileCode size={22} color="var(--accent-primary)" />
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{activeFileInfo.name}</h3>
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Path: <code style={{ color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>{activeFileInfo.path}</code>
                </div>
              </div>

              {onSelectFileNode && (
                <button
                  type="button"
                  onClick={() => onSelectFileNode(activeFileInfo.path)}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(139, 92, 246, 0.15)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    color: '#c084fc',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                  }}
                >
                  <span>Focus in Graph</span>
                  <ArrowRight size={14} />
                </button>
              )}
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Box size={18} color="var(--accent-purple)" />
                <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Classes ({activeClasses.length})</h4>
              </div>
              {activeClasses.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
                  {activeClasses.map((cls, idx) => (
                    <div key={idx} style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(9, 13, 22, 0.6)', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontWeight: 600, color: '#c084fc', fontSize: '0.9rem' }}>{cls.name}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
                        Lines {cls.start_line} - {cls.end_line}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>No class declarations found in this file.</div>
              )}
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Cpu size={18} color="var(--accent-emerald)" />
                <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Functions & Handlers ({activeFunctions.length})</h4>
              </div>
              {activeFunctions.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '0.75rem' }}>
                  {activeFunctions.map((fn, idx) => (
                    <div key={idx} style={{ padding: '0.75rem', borderRadius: '8px', backgroundColor: 'rgba(9, 13, 22, 0.6)', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontWeight: 600, color: '#34d399', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', wordBreak: 'break-word' }}>
                        {fn.name}({fn.parameters.join(', ')})
                      </div>
                      {fn.containing_class && (
                        <div style={{ fontSize: '0.75rem', color: '#c084fc', marginTop: '0.15rem' }}>
                          Class: {fn.containing_class}
                        </div>
                      )}
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
                        Lines {fn.start_line} - {fn.end_line}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>No function declarations found in this file.</div>
              )}
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Layers size={18} color="var(--accent-amber)" />
                <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Dependencies ({activeDependencies.length} outgoing, {activeIncomingDependencies.length} incoming)</h4>
              </div>
              
              {activeDependencies.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>Dependencies:</div>
                  {activeDependencies.map((dep, idx) => (
                    <div key={idx} style={{ padding: '0.6rem 0.8rem', borderRadius: '6px', backgroundColor: 'rgba(9, 13, 22, 0.6)', border: '1px solid var(--border-color)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.85rem', color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>{dep.target_file}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{dep.import_statement}</span>
                    </div>
                  ))}
                </div>
              )}

              {activeIncomingDependencies.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>Depended on by:</div>
                  {activeIncomingDependencies.map((dep, idx) => (
                    <div key={idx} style={{ padding: '0.6rem 0.8rem', borderRadius: '6px', backgroundColor: 'rgba(9, 13, 22, 0.6)', border: '1px solid var(--border-color)', marginBottom: '0.4rem' }}>
                      <span style={{ fontSize: '0.85rem', color: '#f472b6', fontFamily: 'var(--font-mono)' }}>{dep.source_file}</span>
                    </div>
                  ))}
                </div>
              )}

              {activeDependencies.length === 0 && activeIncomingDependencies.length === 0 && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>No file-level dependencies detected for this file.</div>
              )}
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-dim)', marginTop: '4rem' }}>
            Select a file from the sidebar to inspect AST details.
          </div>
        )}
      </div>
    </div>
  );
};
