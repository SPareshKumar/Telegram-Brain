from fastapi import APIRouter, Response, status
from fastapi.responses import HTMLResponse
from app.db.supabase_client import get_db

router = APIRouter(prefix="/ui", tags=["Dashboard"])

@router.get("/api/graph/{telegram_id}")
async def get_user_graph(telegram_id: int):
    db = get_db()
    nodes_res = db.table("nodes").select("*").eq("telegram_id", telegram_id).execute()
    edges_res = db.table("edges").select("*").eq("telegram_id", telegram_id).execute()
    
    formatted_nodes = []
    for n in nodes_res.data:
        node_name = n["entity_name"]
        group_type = "SECURE_VAULT" if "[SECURE_VAULT_REF]" in node_name or "id card" in node_name.lower() else n["entity_type"]
        
        formatted_nodes.append({
            "id": node_name,
            "group": group_type
        })
        
    graph_data = {
        "nodes": formatted_nodes,
        "links": [{"source": e["source_entity_name"], "target": e["target_entity_name"], "label": e["relationship"]} for e in edges_res.data]
    }
    
    unique_nodes = list({v['id']:v for v in graph_data["nodes"]}.values())
    graph_data["nodes"] = unique_nodes
    return graph_data

# 🚀 NEW ROUTE: Fetch Telemetry logs from Supabase
@router.get("/api/logs/{telegram_id}")
async def get_telemetry_logs(telegram_id: int):
    db = get_db()
    logs_res = db.table("evaluation_logs")\
                 .select("created_at, query, response, context_relevance, groundedness, reasoning")\
                 .eq("telegram_id", telegram_id)\
                 .order("created_at", desc=True)\
                 .limit(5)\
                 .execute()
    return logs_res.data

@router.get("/dashboard/{telegram_id}")
async def view_dashboard(telegram_id: int):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Digital Mind</title>
        <script src="https://unpkg.com/force-graph"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #080b10;
                --panel-bg: rgba(13, 20, 30, 0.6);
                --border-color: rgba(255, 255, 255, 0.1);
                --text-primary: #f0f4f8;
                --text-secondary: #8a99ad;
                --accent-blue: #38bdf8;
            }}
            
            body {{
                margin: 0;
                padding: 0;
                background-color: var(--bg-color);
                color: var(--text-primary);
                font-family: 'Inter', sans-serif;
                overflow: hidden;
            }}
            
            #graph-container {{
                width: 100vw;
                height: 100vh;
                position: absolute;
                top: 0;
                left: 0;
                z-index: 1;
            }}
            
            #glass-panel {{
                position: absolute;
                top: 24px;
                left: 24px;
                width: 320px;
                max-height: calc(100vh - 80px);
                background: var(--panel-bg);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 24px;
                z-index: 10;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                display: flex;
                flex-direction: column;
            }}
            
            h1 {{
                margin: 0 0 8px 0;
                font-size: 22px;
                font-weight: 600;
                color: #ffffff;
            }}
            
            .meta-tag {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: var(--text-secondary);
                margin-bottom: 20px;
            }}
            
            .stats-container {{
                border-top: 1px solid var(--border-color);
                padding-top: 16px;
                margin-top: 16px;
            }}
            
            .stat-row {{
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                margin-bottom: 8px;
                color: var(--text-secondary);
            }}
            
            .stat-value {{
                color: var(--text-primary);
                font-family: 'JetBrains Mono', monospace;
                font-weight: 600;
            }}

            /* 🎛️ COCKPIT LOG STYLES */
            .logs-title {{
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--accent-blue);
                margin-top: 24px;
                margin-bottom: 12px;
                border-top: 1px solid var(--border-color);
                padding-top: 16px;
            }}

            .log-stream {{
                flex-grow: 1;
                overflow-y: auto;
                padding-right: 4px;
            }}

            .log-card {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid var(--border-color);
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 12px;
                font-size: 12px;
            }}

            .log-query {{
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 4px;
            }}

            .log-metrics {{
                display: flex;
                gap: 12px;
                margin-top: 8px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
            }}

            .metric-badge {{
                padding: 2px 6px;
                border-radius: 4px;
                background: rgba(56, 189, 248, 0.1);
                color: var(--accent-blue);
            }}

            .metric-badge.good {{
                background: rgba(16, 185, 129, 0.1);
                color: #10b981;
            }}

            .metric-badge.bad {{
                background: rgba(239, 68, 68, 0.1);
                color: #ef4444;
            }}
            
            .log-reasoning {{
                font-size: 11px;
                color: var(--text-secondary);
                margin-top: 6px;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div id="glass-panel">
            <h1>Digital Mind</h1>
            <div class="meta-tag">ID: {telegram_id}</div>
            
            <div class="stats-container">
                <div class="stat-row">
                    <span>System Status</span>
                    <span class="stat-value" style="color: #10b981;">● Active</span>
                </div>
                <div class="stat-row">
                    <span>Knowledge Nodes</span>
                    <span class="stat-value" id="node-count">...</span>
                </div>
            </div>

            <!-- 📡 LOG CONSOLE HOLDER -->
            <div class="logs-title">RAG Observability Telemetry</div>
            <div class="log-stream" id="log-stream">
                <div style="color: var(--text-secondary); font-size: 12px;">Awaiting telemetry frame...</div>
            </div>
        </div>
        
        <div id="graph-container"></div>

        <script>
            // Fetch Graph Structure
            fetch('/ui/api/graph/{telegram_id}')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('node-count').innerText = data.nodes.length;
                    
                    const container = document.getElementById('graph-container');
                    const Graph = ForceGraph()(container)
                        .graphData(data)
                        .nodeId('id')
                        .linkWidth(1.5)
                        .linkColor(() => 'rgba(255, 255, 255, 0.15)')
                        .backgroundColor('#080b10')
                        .cooldownTicks(Infinity)
                        .onNodeDragEnd(node => {{
                            node.fx = node.x;
                            node.fy = node.y;
                        }})
                        .onNodeClick(node => {{
                            node.fx = undefined;
                            node.fy = undefined;
                        }});

                    Graph.d3Force('charge').strength(-250);
                    Graph.d3Force('link').distance(50).strength(0.2);
                    
                    Graph.d3Force('brain-lobes', (alpha) => {{
                        data.nodes.forEach((node, index) => {{
                            const isStem = index % 5 === 0;
                            const isLeft = index % 2 === 0;
                            let targetX = isLeft ? -90 : 90;
                            let targetY = -40;
                            if (isStem) {{
                                targetX = 0;
                                targetY = 120;
                            }}
                            node.vx += (targetX - node.x) * 0.05 * alpha;
                            node.vy += (targetY - node.y) * 0.05 * alpha;
                        }});
                    }});

                    let hoveredNode = null;
                    Graph.onNodeHover(node => {{
                        container.style.cursor = node ? 'pointer' : 'default';
                        hoveredNode = node;
                    }});

                    Graph.nodeCanvasObject((node, ctx, globalScale) => {{
                        const isSecure = node.group === "SECURE_VAULT";
                        const isHovered = hoveredNode === node;
                        let coreColor = isSecure ? '#ef4444' : '#3b82f6';
                        if (node.group === "Technology" || node.group === "Stack") coreColor = '#8b5cf6';
                        if (node.group === "Concept") coreColor = '#10b981';
                        
                        const radius = isHovered ? 6 : 4;
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                        ctx.fillStyle = coreColor;
                        ctx.fill();
                        
                        const rawLabel = node.id.replace("[SECURE_VAULT_REF] ", "🔒 ");
                        const label = rawLabel.length > 25 ? rawLabel.substring(0, 22) + '...' : rawLabel;
                        const fontSize = isHovered ? 14 / globalScale : 12 / globalScale;
                        ctx.font = `${{fontSize}}px 'Inter'`;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'top';
                        
                        ctx.fillStyle = 'rgba(8, 11, 16, 0.9)';
                        const textWidth = ctx.measureText(label).width;
                        ctx.fillRect(node.x - textWidth/2 - 2, node.y + radius + 2, textWidth + 4, fontSize + 4);
                        
                        ctx.fillStyle = isHovered ? '#ffffff' : '#9ca3af';
                        ctx.fillText(label, node.x, node.y + radius + 4);
                    }});
                }})
                .catch(err => console.error(err));

            // 📡 FETCH AND INJECT LIVE REAL-TIME TELEMETRY LOGS
            fetch('/ui/api/logs/{telegram_id}')
                .then(res => res.json())
                .then(logs => {{
                    const stream = document.getElementById('log-stream');
                    if(logs.length === 0) {{
                        stream.innerHTML = '<div style="color: var(--text-secondary); font-size: 12px;">No evaluation traces compiled yet.</div>';
                        return;
                    }}
                    stream.innerHTML = '';
                    logs.forEach(log => {{
                        const relClass = log.context_relevance >= 0.7 ? 'good' : (log.context_relevance <= 0.3 ? 'bad' : '');
                        const grdClass = log.groundedness >= 0.7 ? 'good' : (log.groundedness <= 0.3 ? 'bad' : '');
                        
                        const card = document.createElement('div');
                        card.className = 'log-card';
                        card.innerHTML = `
                            <div class="log-query">🔮 Q: "${{log.query}}"</div>
                            <div style="color: var(--text-secondary); line-height: 1.4;">🤖 A: ${{log.response.substring(0, 60)}}${{log.response.length > 60 ? '...' : ''}}</div>
                            <div class="log-metrics">
                                <span class="metric-badge ${{relClass}}">CR: ${{log.context_relevance.toFixed(2)}}</span>
                                <span class="metric-badge ${{grdClass}}">GD: ${{log.groundedness.toFixed(2)}}</span>
                            </div>
                            <div class="log-reasoning">⚖️ ${{log.reasoning || 'No metadata reasoning available.'}}</div>
                        `;
                        stream.appendChild(card);
                    }});
                }})
                .catch(err => console.error(err));
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)