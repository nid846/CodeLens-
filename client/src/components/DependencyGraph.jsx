import React, { useState, useMemo, useCallback, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { Search, Maximize2, RefreshCw, Layers, ArrowUpRight, ArrowDownLeft, X } from 'lucide-react';

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, ranksep: 80, nodesep: 40 });

  const nodeWidth = 180;
  const nodeHeight = 50;

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      targetPosition: direction === 'TB' ? 'top' : 'left',
      sourcePosition: direction === 'TB' ? 'bottom' : 'right',
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

export const DependencyGraph = ({ graphData, onSelectFile }) => {
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [layoutDir, setLayoutDir] = useState('TB'); // 'TB' (top-bottom) or 'LR' (left-right)

  const initialElements = useMemo(() => {
    if (!graphData || !graphData.nodes) return { nodes: [], edges: [] };

    const rfNodes = graphData.nodes.map((node) => {
      const isPy = node.language === 'Python';
      const isJava = node.language === 'Java';
      const isJs = node.language === 'JavaScript' || node.language === 'TypeScript';

      let borderColor = '#3b82f6';
      if (isPy) borderColor = '#3b82f6';
      else if (isJava) borderColor = '#f59e0b';
      else if (isJs) borderColor = '#10b981';

      return {
        id: node.id,
        data: { label: node.label, path: node.id, language: node.language },
        style: {
          background: 'rgba(18, 26, 43, 0.95)',
          color: '#ffffff',
          border: `1.5px solid ${borderColor}`,
          borderRadius: '10px',
          padding: '8px 14px',
          fontSize: '12px',
          fontWeight: 600,
          boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
          width: 180,
          cursor: 'pointer',
        },
      };
    });

    const rfEdges = (graphData.edges || []).map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      animated: true,
      style: { stroke: 'rgba(255, 255, 255, 0.25)', strokeWidth: 1.5 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: 'rgba(255, 255, 255, 0.4)',
        width: 14,
        height: 14,
      },
    }));

    return getLayoutedElements(rfNodes, rfEdges, layoutDir);
  }, [graphData, layoutDir]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialElements.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialElements.edges);

  useEffect(() => {
    setNodes(initialElements.nodes);
    setEdges(initialElements.edges);
  }, [initialElements, setNodes, setEdges]);

  // Handle node selection & highlighting connected nodes & edges
  const handleNodeClick = useCallback(
    (_, node) => {
      setSelectedNodeId(node.id);
      if (onSelectFile) onSelectFile(node.id);
    },
    [onSelectFile]
  );

  const resetSelection = () => {
    setSelectedNodeId(null);
  };

  // Calculate highlighted state for nodes & edges
  const { highlightedNodes, highlightedEdges } = useMemo(() => {
    if (!selectedNodeId) {
      return { highlightedNodes: nodes, highlightedEdges: edges };
    }

    const connectedNodeIds = new Set([selectedNodeId]);
    const connectedEdgeIds = new Set();

    edges.forEach((edge) => {
      if (edge.source === selectedNodeId) {
        connectedNodeIds.add(edge.target);
        connectedEdgeIds.add(edge.id);
      } else if (edge.target === selectedNodeId) {
        connectedNodeIds.add(edge.source);
        connectedEdgeIds.add(edge.id);
      }
    });

    const updatedNodes = nodes.map((node) => {
      const isMatchSearch = searchTerm
        ? node.data.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
          node.data.path.toLowerCase().includes(searchTerm.toLowerCase())
        : true;

      const isConnected = connectedNodeIds.has(node.id) && isMatchSearch;
      const isSelected = node.id === selectedNodeId;

      return {
        ...node,
        style: {
          ...node.style,
          opacity: isConnected ? 1 : 0.2,
          border: isSelected
            ? '2.5px solid #ec4899'
            : isConnected
            ? '2px solid #3b82f6'
            : '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: isSelected
            ? '0 0 20px rgba(236, 72, 153, 0.6)'
            : isConnected
            ? '0 0 12px rgba(59, 130, 246, 0.4)'
            : 'none',
        },
      };
    });

    const updatedEdges = edges.map((edge) => {
      const isConnected = connectedEdgeIds.has(edge.id);
      return {
        ...edge,
        animated: isConnected,
        style: {
          stroke: isConnected ? '#ec4899' : 'rgba(255, 255, 255, 0.08)',
          strokeWidth: isConnected ? 2.5 : 1,
        },
        markerEnd: {
          ...edge.markerEnd,
          color: isConnected ? '#ec4899' : 'rgba(255, 255, 255, 0.15)',
        },
      };
    });

    return { highlightedNodes: updatedNodes, highlightedEdges: updatedEdges };
  }, [selectedNodeId, searchTerm, nodes, edges]);

  // Details of currently selected node
  const selectedNodeInfo = useMemo(() => {
    if (!selectedNodeId || !graphData) return null;
    const node = graphData.nodes.find((n) => n.id === selectedNodeId);
    if (!node) return null;

    const outgoing = (graphData.edges || []).filter((e) => e.source === selectedNodeId);
    const incoming = (graphData.edges || []).filter((e) => e.target === selectedNodeId);

    return { ...node, outgoing, incoming };
  }, [selectedNodeId, graphData]);

  return (
    <div className="glass-panel" style={{ height: '650px', position: 'relative', overflow: 'hidden' }}>
      <ReactFlow
        nodes={highlightedNodes}
        edges={highlightedEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={resetSelection}
        fitView
      >
        <Background color="rgba(255, 255, 255, 0.05)" gap={20} size={1} />
        <Controls style={{ backgroundColor: 'rgba(18, 26, 43, 0.9)', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
        <MiniMap
          style={{ backgroundColor: 'rgba(9, 13, 22, 0.9)', borderRadius: '8px', border: '1px solid var(--border-color)' }}
          nodeColor={(n) => (n.id === selectedNodeId ? '#ec4899' : '#3b82f6')}
        />

        {/* Top Control Bar Panel */}
        <Panel position="top-left" style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
            <input
              type="text"
              placeholder="Search node..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                padding: '0.45rem 0.75rem 0.45rem 2rem',
                borderRadius: '8px',
                backgroundColor: 'rgba(18, 26, 43, 0.9)',
                border: '1px solid var(--border-color)',
                color: '#ffffff',
                fontSize: '0.82rem',
                width: '180px',
              }}
            />
          </div>

          <button
            type="button"
            onClick={() => setLayoutDir((d) => (d === 'TB' ? 'LR' : 'TB'))}
            style={{
              padding: '0.45rem 0.85rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(18, 26, 43, 0.9)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <RefreshCw size={14} />
            <span>Layout: {layoutDir === 'TB' ? 'Top-Down' : 'Left-Right'}</span>
          </button>
        </Panel>

        {/* Selected Node Details Floating Overlay Panel */}
        {selectedNodeInfo && (
          <Panel position="top-right" style={{ width: '300px', margin: '0' }}>
            <div className="glass-panel animate-fade-in" style={{ padding: '1rem', backgroundColor: 'rgba(9, 13, 22, 0.95)', border: '1px solid rgba(236, 72, 153, 0.4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ec4899', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Node Inspector
                </div>
                <button type="button" onClick={resetSelection} style={{ background: 'none', color: 'var(--text-muted)' }}>
                  <X size={16} />
                </button>
              </div>

              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', wordBreak: 'break-all', marginBottom: '0.3rem' }}>
                {selectedNodeInfo.label}
              </h4>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', wordBreak: 'break-all', marginBottom: '0.75rem' }}>
                {selectedNodeInfo.id}
              </div>

              {/* Outgoing Dependencies */}
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '0.78rem', color: '#60a5fa', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.3rem' }}>
                  <ArrowUpRight size={14} />
                  <span>Imports ({selectedNodeInfo.outgoing.length}):</span>
                </div>
                {selectedNodeInfo.outgoing.map((e, idx) => (
                  <div key={idx} style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '0.2rem 0.4rem', borderRadius: '4px', backgroundColor: 'rgba(255, 255, 255, 0.05)', marginBottom: '0.2rem', wordBreak: 'break-all' }}>
                    {e.target}
                  </div>
                ))}
                {selectedNodeInfo.outgoing.length === 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>None</div>
                )}
              </div>

              {/* Incoming Dependencies */}
              <div>
                <div style={{ fontSize: '0.78rem', color: '#f472b6', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.3rem' }}>
                  <ArrowDownLeft size={14} />
                  <span>Imported By ({selectedNodeInfo.incoming.length}):</span>
                </div>
                {selectedNodeInfo.incoming.map((e, idx) => (
                  <div key={idx} style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '0.2rem 0.4rem', borderRadius: '4px', backgroundColor: 'rgba(255, 255, 255, 0.05)', marginBottom: '0.2rem', wordBreak: 'break-all' }}>
                    {e.source}
                  </div>
                ))}
                {selectedNodeInfo.incoming.length === 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>None</div>
                )}
              </div>
            </div>
          </Panel>
        )}
      </ReactFlow>
    </div>
  );
};
