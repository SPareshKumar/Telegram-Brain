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
        <title>Digital Brain Topology</title>
        <script src="https://unpkg.com/force-graph"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #080b10;
                --panel-bg: rgba(13, 20, 30, 0.45);
                --border-color: rgba(255, 255, 255, 0.06);
                --text-primary: #f0f4f8;
                --text-secondary: #8a99ad;
                --accent-blue: #38bdf8;
                --accent-secure: #f43f5e;
            }}
            
            body {{
                margin: 0;
                padding: 0;
                background-color: var(--bg-color);
                color: var(--text-primary);
                font-family: 'Inter', sans-serif;
                overflow: hidden;
                background-image: 
                    linear-gradient(rgba(255,255,255,0.01) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.01) 1px, transparent 1px);
                background-size: 40px 40px;
            }}
            
            #graph-container {{
                width: 100vw;
                height: 100vh;
                position: absolute;
                top: 0;
                left: 0;
                z-index: 1;
            }}
            
            /* Modern Glassmorphic Side Panel */
            #glass-panel {{
                position: absolute;
                top: 24px;
                left: 24px;
                width: 320px;
                background: var(--panel-bg);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 24px;
                z-index: 10;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                pointer-events: auto;
            }}
            
            h1 {{
                margin: 0 0 6px 0;
                font-size: 20px;
                font-weight: 600;
                letter-spacing: -0.5px;
                background: linear-gradient(135deg, #fff 0%, var(--text-secondary) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            .meta-tag {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: var(--accent-blue);
                background: rgba(56, 189, 248, 0.1);
                padding: 2px 8px;
                border-radius: 4px;
                display: inline-block;
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
            
            /* Custom minimalist tooltip */
            .graph-tooltip {{
                background: rgba(10, 15, 26, 0.9) !important;
                border: 1px solid var(--border-color) !important;
                backdrop-filter: blur(8px);
                border-radius: 8px !important;
                padding: 8px 12px !important;
                font-size: 12px !important;
                color: var(--text-primary) !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            }}
        </style>
    </head>
    <body>
        <div id="glass-panel">
            <h1>CORTICAL REPOSITORY</h1>
            <div class="meta-tag">BRAIN_ID // {telegram_id}</div>
            
            <div class="stats-container">
                <div class="stat-row">
                    <span>Status</span>
                    <span class="stat-value" style="color: #10b981;">● ONLINE</span>
                </div>
                <div class="stat-row">
                    <span>Topology Geometry</span>
                    <span class="stat-value">Bi-Hemispheric</span>
                </div>
                <div class="stat-row">
                    <span>Sync Metrics</span>
                    <span class="stat-value" id="node-count">Calculating...</span>
                </div>
            </div>
        </div>
        
        <div id="graph-container"></div>

        <script>
            fetch('/ui/api/graph/{telegram_id}')
                .then(res => {{
                    if(!res.ok) throw new Error("Network response was not ok");
                    return res.json();
                }})
                .then(data => {{
                    document.getElementById('node-count').innerText = `${{data.nodes.length}} Nodes`;
                    
                    const container = document.getElementById('graph-container');
                    const Graph = ForceGraph()(container)
                        .graphData(data)
                        .nodeId('id')
                        .linkWidth(1)
                        .linkColor(() => 'rgba(255, 255, 255, 0.07)')
                        .linkDirectionalArrowLength(0) // Minimalist link approach
                        .backgroundColor('#080b10')
                        .cooldownTicks(120);

                    // --- BRAIN GEOMETRY FORCES ---
                    // Custom force system that pulls nodes into an anatomical brain silhouette
                    Graph.d3Force('charge').strength(-45);
                    Graph.d3Force('link').distance(40);
                    
                    // The Cortical Envelope Constellation Multi-Force
                    Graph.d3Force('brain-shape', (alpha) => {{
                        data.nodes.forEach(node => {{
                            // Group 0/even nodes to Left Hemisphere, Group 1/odd to Right Hemisphere
                            const isLeftHemisphere = node.id.charCodeAt(0) % 2 === 0;
                            const targetX = isLeftHemisphere ? -90 : 90;
                            
                            // Create a round sagittal curve envelope (Y-axis squeezing)
                            const targetY = Math.sin(node.x / 60) * 45;
                            
                            // Smoothly drag nodes toward the imaginary geometric envelope
                            node.vx += (targetX - node.x) * 0.02 * alpha;
                            node.vy += (targetY - node.y) * 0.02 * alpha;
                        }});
                    }});

                    // --- HIGH-END HOVER & RENDERING PIPELINE ---
                    let hoveredNode = null;

                    Graph.onNodeHover(node => {{
                        container.style.cursor = node ? 'pointer' : 'default';
                        hoveredNode = node;
                    }});

                    Graph.nodeCanvasObject((node, ctx, globalScale) => {{
                        const isSecure = node.group === "SECURE_VAULT";
                        const isHovered = hoveredNode === node;
                        
                        // Pick aesthetic cyberpunk glowing tones
                        let coreColor = isSecure ? '#f43f5e' : '#38bdf8';
                        if (node.group === "Technology" || node.group === "Stack") coreColor = '#a855f7';
                        if (node.group === "Concept") coreColor = '#34d399';
                        
                        // Particle Glow Ring Effect
                        const radius = isHovered ? 7 : 4.5;
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI, false);
                        ctx.fillStyle = isHovered ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255,255,255,0.01)';
                        ctx.fill();

                        // Core Node Dot
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                        ctx.fillStyle = coreColor;
                        ctx.fill();
                        
                        // High-fidelity Typographic Label Rendering
                        const rawLabel = node.id.replace("[SECURE_VAULT_REF] ", "🔒 ");
                        const label = rawLabel.length > 25 ? rawLabel.substring(0, 22) + '...' : rawLabel;
                        
                        const fontSize = isHovered ? 14 / globalScale : 11 / globalScale;
                        ctx.font = isHovered ? `600 ${{fontSize}}px 'Inter'` : `400 ${{fontSize}}px 'Inter'`;
                        
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'top';
                        
                        // Shadow text backing for extreme readability over overlapping node clusters
                        ctx.fillStyle = 'rgba(8, 11, 16, 0.85)';
                        ctx.fillText(label, node.x, node.y + radius + 3);
                        ctx.fillText(label, node.x - 1, node.y + radius + 3);
                        ctx.fillText(label, node.x + 1, node.y + radius + 3);
                        
                        ctx.fillStyle = isHovered ? '#ffffff' : 'rgba(240, 244, 248, 0.85)';
                        ctx.fillText(label, node.x, node.y + radius + 3);
                    }});
                }})
                .catch(err => {{
                    console.error("Dashboard failed to initialize:", err);
                }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)