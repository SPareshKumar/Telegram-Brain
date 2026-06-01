# MindMap AI 🧠

MindMap AI is a production-grade, asynchronous Retrieval-Augmented Generation (RAG) conversational agent integrated with Telegram. It functions as an intelligent "second brain," capable of contextually routing user requests, handling rolling short-term dialogue, executing semantic vector searches, and securely locking away sensitive information. 

The architecture is built with an emphasis on production resilience, featuring automated multi-model fallback cascades, zero-cost query reformulation, and an asynchronous automated MLOps pipeline using the **RAG Triad (LLM-as-a-Judge)** framework.

---

## 🚀 Core Features

### 1. Dual-Layer Memory Architecture
*   **Short-Term Memory (Context Buffer):** Dynamically queries rolling chat history to inject recent multi-turn context into the generation loop, allowing seamless follow-up interactions.
*   **Long-Term Memory (Semantic Vector Search):** Utilizes `pgvector` inside Supabase to handle 768-dimensional embeddings via a dual-table optimization schema (separating raw data from vector metrics) linked via custom PostgreSQL RPC similarity joins.

### 2. Live Dynamic Brain Visualization Dashboard
*   **Knowledge Graph Extraction:** In tandem with intent parsing, an extraction engine maps unstructured user interactions into structured JSON components (nodes, edges, and relationships).
*   **Interactive Frontend:** A built-in Streamlit and Pyvis dashboard charts a living, interactive network visualization of the user's interconnected memories. Users can explore clusters, look for semantic associations, and physically see how their "second brain" is growing over time.

### 3. Automated MLOps Triad Evaluation (LLM-as-a-Judge)
*   **Zero-Block Asynchronous Workflows:** Evaluation logic is offloaded onto FastAPI `BackgroundTasks` to preserve a sub-second response latency for the user.
*   **Langfuse V3 Integration:** Leveraging the OpenTelemetry tracing standard, a background evaluator model (`gemini-2.5-flash-lite`) mathematically grades every production RAG output for **Context Relevance** and **Groundedness**, immediately streaming telemetry to a centralized observability dashboard.

### 4. Zero-Cost Query Reformulation
*   Resolves pronoun ambiguities (e.g., transforming "where does he live?" into "where does John live?") by passing the short-term context buffer through a unified parsing engine. This ensures semantic database vectors hit the exact mathematical target without requiring an expensive secondary API call.

### 5. Secure Context Vault (In-Memory Cryptography)
*   Automatically flags incoming sensitive data via an automated intent classifier. Sensitive items are encrypted using symmetric AES-256 blocks and written to an isolated secure vault. References are swapped out with semantic pointers in the public table and safely decrypted purely in-RAM during RAG synthesis.

### 6. High-Availability Multi-Model Cascades
*   To shield users from upstream service interruptions, the system captures network exceptions (`429 Quota Exceeded` or `503 Service Unavailable`) on the primary generation tier and dynamically routes traffic down to a lightweight fallback model.

---

## 🛠️ Technical Stack
*   **Language:** Python, PostgreSQL (SQL)
*   **API Framework:** FastAPI, Uvicorn
*   **Database:** Supabase (with `pgvector` extension)
*   **AI/LLM Architecture:** Google Gemini API (`gemini-3.5-flash`, `gemini-2.5-flash-lite`)
*   **Observability/MLOps:** Langfuse V3 (OpenTelemetry client)
*   **Visualization:** Streamlit, Pyvis, NetworkX
*   **Security:** Cryptography (Symmetric Fernet / AES-256)
*   **Containerization & Hosting:** Docker, Render
---
## 🤝 Contributing

Contributions, suggestions, and feedback are always welcome!

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!
