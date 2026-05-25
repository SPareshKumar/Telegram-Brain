import streamlit as st
import datetime

# Page Configuration
st.set_page_config(
    page_title="Digital Second Brain Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern CSS
st.markdown(
    """
    <style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Global styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Custom main gradient header */
    .header-container {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.2);
    }
    .header-container h1 {
        margin: 0;
        font-weight: 800;
        font-size: 2.8rem;
        letter-spacing: -0.5px;
    }
    .header-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 300;
    }
    
    /* Custom metrics cards */
    .metric-card {
        background-color: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -8px rgba(99, 102, 241, 0.5);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.95rem;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 1px;
    }
    .metric-val {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0.5rem 0;
    }
    .metric-delta {
        font-size: 0.9rem;
        font-weight: 600;
    }
    .delta-positive {
        color: #10b981;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Banner
st.markdown(
    """
    <div class="header-container">
        <h1>🧠 Digital Second Brain</h1>
        <p>Your AI-Powered Multimodal Knowledge Graph & Semantic Storage Hub</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar configurations
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1507668077129-56e32842fceb?auto=format&fit=crop&w=300&q=80", use_column_width=True)
    st.markdown("### 🎛️ Control Panel")
    st.info("System initialized successfully. Connect your Telegram bot and Supabase DB to begin syncing.")
    
    st.divider()
    st.markdown("### ⚙️ Environment Configs")
    st.text_input("Supabase Endpoint", value="Connected", disabled=True)
    st.text_input("Gemini Engine", value="Gemini 1.5 Flash", disabled=True)
    
    st.caption("Google Antigravity 2.0 Scaffold v1.0.0")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📊 Brain Analytics", "🕸️ Knowledge Graph", "📥 Direct Ingestion"])

with tab1:
    st.subheader("System Performance & Ingestion Stats")
    
    # 3-column metric display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Total Memories</div>
                <div class="metric-val">142</div>
                <div class="metric-delta delta-positive">▲ +12 this week</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Graph Entities</div>
                <div class="metric-val">389</div>
                <div class="metric-delta delta-positive">▲ +45 relations</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Semantic Queries</div>
                <div class="metric-val">1,024</div>
                <div class="metric-delta delta-positive">▲ 99.4% Latency: 220ms</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.write("")
    st.write("")
    
    # Ingestion activity feed table placeholder
    st.subheader("🕒 Recent Ingested Elements")
    activity_data = [
        {"Timestamp": str(datetime.datetime.now() - datetime.timedelta(minutes=15)), "Type": "📄 PDF", "Description": "Gemini 1.5 Flash Technical Specifications", "Status": "Success"},
        {"Timestamp": str(datetime.datetime.now() - datetime.timedelta(hours=2)), "Type": "🖼️ Image", "Description": "Whiteboard session architecture notes", "Status": "Success"},
        {"Timestamp": str(datetime.datetime.now() - datetime.timedelta(days=1)), "Type": "✍️ Text", "Description": "Reminder: Project milestones for Q2", "Status": "Success"},
    ]
    st.table(activity_data)

with tab2:
    st.subheader("🕸️ Dynamic Network Graph representation")
    st.info("Pyvis interactive network rendering placeholder. Live graph will load when Supabase connection has been populated.")
    # Show placeholder visual element
    st.code(
        """
        # Graph construction code blueprint
        import networkx as nx
        from pyvis.network import Network

        G = nx.Graph()
        G.add_node("User", label="User Profile", color="#4f46e5")
        G.add_node("Doc1", label="Project Specification", color="#db2777")
        G.add_edge("User", "Doc1", title="created")
        """,
        language="python"
    )

with tab3:
    st.subheader("📥 Add memory directly")
    with st.form("ingest_form"):
        title = st.text_input("Title")
        content = st.text_area("Content or Transcript")
        tags = st.text_input("Tags (comma separated)")
        submitted = st.form_submit_button("Ingest to Brain")
        if submitted:
            st.success(f"Scaffold Success: Ingested memory '{title}' (mocked).")

# Global Footer
st.markdown(
    """
    <div class="footer">
        Designed for Agent-First Execution. Powered by Gemini API & Langfuse LLMOps.
    </div>
    """,
    unsafe_allow_html=True
)
