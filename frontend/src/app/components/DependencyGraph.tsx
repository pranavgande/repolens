import { useMemo } from 'react';
import { ReactFlow, Controls, Background, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

export function DependencyGraph({ reactFlowData }: { reactFlowData: { nodes: any[], edges: any[] } }) {
  // reactFlowData already contains the fully laid out nodes and edges from our backend serializer!
  const defaultNodes = useMemo(() => reactFlowData?.nodes || [], [reactFlowData]);
  const defaultEdges = useMemo(() => reactFlowData?.edges || [], [reactFlowData]);

  if (!defaultNodes.length) {
    return <div className="text-center p-8 text-muted-foreground">No dependency data available.</div>;
  }

  return (
    <div className="w-full h-[600px] bg-background border rounded-xl overflow-hidden shadow-inner">
      <ReactFlow
        defaultNodes={defaultNodes}
        defaultEdges={defaultEdges}
        fitView
        attributionPosition="bottom-right"
        className="dark:bg-background"
      >
        <Controls />
        <Background gap={12} size={1} />
        <MiniMap 
           nodeStrokeColor={(n) => {
             if (n.type === 'input') return '#f97316';
             return '#e2e8f0';
           }}
           nodeColor={(n) => {
             return '#334155';
           }}
           maskColor="rgba(0, 0, 0, 0.2)"
        />
      </ReactFlow>
    </div>
  );
}
