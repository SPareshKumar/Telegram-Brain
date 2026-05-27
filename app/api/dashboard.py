from fastapi import APIRouter, Request, Response, status
from fastapi.responses import HTMLResponse
# ... (your existing imports)

# 1. The API endpoint to fetch graph data
@router.get("/api/graph/{telegram_id}")
async def get_user_graph(telegram_id: int):
    """
    Fetches all nodes and edges for a specific user and formats 
    them for the frontend force-graph library.
    """
    db = get_db()
    
    # Fetch data
    nodes_res = db.table("nodes").select("*").eq("telegram_id", telegram_id).execute()
    edges_res = db.table("edges").select("*").eq("telegram_id", telegram_id).execute()
    
    # Format for D3 / force-graph (requires 'id' for nodes, and 'source'/'target' for links)
    graph_data = {
        "nodes": [{"id": n["entity_name"], "group": n["entity_type"]} for n in nodes_res.data],
        "links": [{"source": e["source_entity_name"], "target": e["target_entity_name"], "label": e["relationship"]} for e in edges_res.data]
    }
    
    # Ensure no duplicate nodes exist
    unique_nodes = list({v['id']:v for v in graph_data["nodes"]}.values())
    graph_data["nodes"] = unique_nodes
    
    return graph_data

# 2. The Web Dashboard Endpoint
@router.get("/dashboard/{telegram_id}")
async def view_dashboard(telegram_id: int):
    """
    Serves the interactive frontend visualizing the user's mind map.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Second Brain</title>
        <script src="https://unpkg.com/force-graph"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: #0d1117; color: white; font-family: sans-serif; }}
            #graph-container {{ width: 100vw; height: 100vh; }}
            #header {{ position: absolute; top: 20px; left: 20px; z-index: 10; }}
            h1 {{ margin: 0; font-size: 24px; color: #58a6ff; }}
        </style>
    </head>
    <body>
        <div id="header">
            <h1>Graph of Mind</h1>
            <p>ID: {telegram_id}</p>
        </div>
        <div id="graph-container"></div>

        <script>
            // Fetch the data from our new API endpoint
            fetch('/telegram/api/graph/{telegram_id}')
                .then(res => res.json())
                .then(data => {{
                    // Initialize the interactive graph
                    const Graph = ForceGraph()
                    (document.getElementById('graph-container'))
                        .graphData(data)
                        .nodeId('id')
                        .nodeAutoColorBy('group')
                        .nodeLabel('id')
                        .linkDirectionalArrowLength(3.5)
                        .linkDirectionalArrowRelPos(1)
                        .linkLabel('label')
                        .onNodeDragEnd(node => {{
                            node.fx = node.x;
                            node.fy = node.y;
                        }});
                        
                    // Add text to the nodes
                    Graph.nodeCanvasObject((node, ctx, globalScale) => {{
                        const label = node.id;
                        const fontSize = 12/globalScale;
                        ctx.font = `${{fontSize}}px Sans-Serif`;
                        const textWidth = ctx.measureText(label).width;
                        const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); 

                        ctx.fillStyle = 'rgba(13, 17, 23, 0.8)';
                        ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);

                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = node.color;
                        ctx.fillText(label, node.x, node.y);
                        
                        node.__bckgDimensions = bckgDimensions; 
                    }});
                }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)