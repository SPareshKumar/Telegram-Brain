from fastapi import APIRouter, Response, status
from fastapi.responses import HTMLResponse
from app.db.supabase_client import get_db

# 💡 THIS IS THE CRUCIAL LINE THAT IS MISSING OR MISPLACED:
router = APIRouter(prefix="/ui", tags=["Dashboard"])

@router.get("/api/graph/{telegram_id}")
async def get_user_graph(telegram_id: int):
    db = get_db()
    nodes_res = db.table("nodes").select("*").eq("telegram_id", telegram_id).execute()
    edges_res = db.table("edges").select("*").eq("telegram_id", telegram_id).execute()
    
    graph_data = {
        "nodes": [{"id": n["entity_name"], "group": n["entity_type"]} for n in nodes_res.data],
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
            fetch('/ui/api/graph/{telegram_id}')
                .then(res => res.json())
                .then(data => {{
                    const Graph = ForceGraph()
                    (document.getElementById('graph-container'))
                        .graphData(data)
                        .nodeId('id')
                        .nodeAutoColorBy('group')
                        .nodeLabel('id')
                        .linkColor(() => '#ffffff')
                        .linkDirectionalArrowLength(3.5)
                        .linkDirectionalArrowColor(() => '#ffffff')
                        .linkDirectionalArrowRelPos(1)
                        .linkLabel('label')
                        .onNodeDragEnd(node => {{
                            node.fx = node.x;
                            node.fy = node.y;
                        }});
                        
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