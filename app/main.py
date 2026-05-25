import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Digital Second Brain API",
    description="Multimodal Knowledge Graph ingestion and semantic query backend.",
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
def root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Digital Second Brain API</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
                --card-bg: rgba(30, 41, 59, 0.7);
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --accent: #6366f1;
                --accent-gradient: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
                --border-color: rgba(255, 255, 255, 0.1);
            }
            body {
                margin: 0;
                padding: 0;
                font-family: 'Outfit', sans-serif;
                background: var(--bg-gradient);
                color: var(--text-main);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }
            .container {
                max-width: 600px;
                padding: 3rem;
                background: var(--card-bg);
                backdrop-filter: blur(10px);
                border: 1px solid var(--border-color);
                border-radius: 24px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                text-align: center;
                animation: fadeIn 0.8s ease-out;
            }
            h1 {
                margin-top: 0;
                font-size: 2.5rem;
                font-weight: 800;
                background: var(--accent-gradient);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 1rem;
            }
            p {
                color: var(--text-muted);
                font-size: 1.1rem;
                line-height: 1.6;
                margin-bottom: 2rem;
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: rgba(16, 185, 129, 0.2);
                border: 1px solid rgba(16, 185, 129, 0.4);
                color: #34d399;
                padding: 0.5rem 1rem;
                border-radius: 9999px;
                font-weight: 600;
                font-size: 0.9rem;
                margin-bottom: 2rem;
            }
            .status-dot {
                width: 8px;
                height: 8px;
                background-color: #10b981;
                border-radius: 50%;
                box-shadow: 0 0 8px #10b981;
                animation: pulse 1.5s infinite;
            }
            .links {
                display: flex;
                justify-content: center;
                gap: 1rem;
            }
            a {
                color: var(--text-main);
                text-decoration: none;
                font-weight: 600;
                padding: 0.75rem 1.5rem;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border-color);
                transition: all 0.3s ease;
            }
            a:hover {
                background: var(--accent-gradient);
                border-color: transparent;
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(99, 102, 241, 0.4);
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes pulse {
                0% { transform: scale(0.9); opacity: 0.6; }
                50% { transform: scale(1.1); opacity: 1; }
                100% { transform: scale(0.9); opacity: 0.6; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Digital Second Brain</h1>
            <div class="status-badge">
                <span class="status-dot"></span>
                API is Active
            </div>
            <p>
                Welcome to the multimodal ingestion API. This backend securely stores your data in Supabase, extracts semantic entities with Gemini, and constructs your personalized Knowledge Graph.
            </p>
            <div class="links">
                <a href="/docs">Interactive Docs</a>
                <a href="/health">Health Status</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Digital Second Brain API"
    }
