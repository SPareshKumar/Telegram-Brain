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
                width: 280px;
                background: var(--panel-bg);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 24px;
                z-index: 10;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
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
        </div>
        
        <div id="graph-container"></div>

        <script>
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
                        .cooldownTicks(Infinity) // Prevents the engine from freezing, fixing the drag bug
                        .onNodeDragEnd(node => {{
                            // Pin node where dropped
                            node.fx = node.x;
                            node.fy = node.y;
                        }})
                        .onNodeClick(node => {{
                            // Unpin node on click so it floats back into the cluster
                            node.fx = undefined;
                            node.fy = undefined;
                        }});

                    // 1. Base physics: nodes repel strongly so they don't clump
                    Graph.d3Force('charge').strength(-250);
                    Graph.d3Force('link').distance(50).strength(0.2);
                    
                    // 2. Custom Brain Geometry Force
                    Graph.d3Force('brain-lobes', (alpha) => {{
                        data.nodes.forEach((node, index) => {{
                            // Designate 1 in every 5 nodes to pull downwards forming a "stem"
                            const isStem = index % 5 === 0;
                            // Split the remaining nodes into left and right hemispheres
                            const isLeft = index % 2 === 0;
                            
                            let targetX = isLeft ? -90 : 90;
                            let targetY = -40;
                            
                            if (isStem) {{
                                targetX = 0;
                                targetY = 120;
                            }}

                            // Apply the pull
                            node.vx += (targetX - node.x) * 0.05 * alpha;
                            node.vy += (targetY - node.y) * 0.05 * alpha;
                        }});
                    }});

                    // 3. Hover & Label Rendering
                    let hoveredNode = null;
                    Graph.onNodeHover(node => {{
                        container.style.cursor = node ? 'pointer' : 'default';
                        hoveredNode = node;
                    }});

                    Graph.nodeCanvasObject((node, ctx, globalScale) => {{
                        const isSecure = node.group === "SECURE_VAULT";
                        const isHovered = hoveredNode === node;
                        
                        let coreColor = isSecure ? '#ef4444' : '#3b82f6'; // Clean red or blue
                        if (node.group === "Technology" || node.group === "Stack") coreColor = '#8b5cf6'; // Purple
                        if (node.group === "Concept") coreColor = '#10b981'; // Green
                        
                        const radius = isHovered ? 6 : 4;
                        
                        // Node circle
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                        ctx.fillStyle = coreColor;
                        ctx.fill();
                        
                        // Label rendering
                        const rawLabel = node.id.replace("[SECURE_VAULT_REF] ", "🔒 ");
                        const label = rawLabel.length > 25 ? rawLabel.substring(0, 22) + '...' : rawLabel;
                        
                        const fontSize = isHovered ? 14 / globalScale : 12 / globalScale;
                        ctx.font = `${{fontSize}}px 'Inter'`;
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'top';
                        
                        // Background shadow for text readability
                        ctx.fillStyle = 'rgba(8, 11, 16, 0.9)';
                        const textWidth = ctx.measureText(label).width;
                        ctx.fillRect(node.x - textWidth/2 - 2, node.y + radius + 2, textWidth + 4, fontSize + 4);
                        
                        // Text itself
                        ctx.fillStyle = isHovered ? '#ffffff' : '#9ca3af';
                        ctx.fillText(label, node.x, node.y + radius + 4);
                    }});
                }})
                .catch(err => console.error(err));
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)