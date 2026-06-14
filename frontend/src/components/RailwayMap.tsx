import type { NetworkEdge, NetworkNode } from "../types";

function delayColor(delay: number) {
  if (delay < 12) return "#2f855a";
  if (delay < 30) return "#b7791f";
  if (delay < 60) return "#c05621";
  return "#b42318";
}

export function RailwayMap({ nodes, edges }: { nodes: NetworkNode[]; edges: NetworkEdge[] }) {
  const nodeIndex = new Map(nodes.map((node) => [node.id, node]));

  return (
    <div className="map-panel">
      <svg viewBox="0 0 100 100" role="img" aria-label="Railway delay map">
        <path
          className="india-outline"
          d="M37 10 L52 12 L62 20 L71 25 L80 39 L76 53 L68 62 L63 75 L54 93 L45 89 L39 79 L29 71 L24 58 L17 46 L22 34 L30 27 Z"
        />
        {edges.map((edge) => {
          const source = nodeIndex.get(edge.source);
          const target = nodeIndex.get(edge.target);
          if (!source || !target) return null;
          return (
            <line
              key={`${edge.source}-${edge.target}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              strokeWidth={Math.min(1.8, 0.45 + edge.trains / 55)}
              className="route-edge"
            />
          );
        })}
        {nodes.map((node) => (
          <g key={node.id}>
            <circle cx={node.x} cy={node.y} r="1.9" fill={delayColor(node.average_delay)} className="station-node">
              <title>{`${node.name} | ${node.average_delay} min`}</title>
            </circle>
            <text x={node.x + 2.4} y={node.y + 0.9} className="map-label">
              {node.id}
            </text>
          </g>
        ))}
      </svg>
      <div className="map-legend" aria-label="Delay legend">
        <span>
          <i className="dot good" /> On time
        </span>
        <span>
          <i className="dot warning" /> Watch
        </span>
        <span>
          <i className="dot severe" /> Severe
        </span>
      </div>
    </div>
  );
}
