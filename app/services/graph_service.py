import networkx as nx
from app.db.supabase_client import get_db

def build_and_traverse_graph(telegram_id: int, query_text: str) -> list[str]:
    """
    Pulls the user's relationships from Supabase, builds a NetworkX graph, 
    and extracts relevant connections based on the user's query.
    """
    db = get_db()
    
    # 1. Fetch all edges for this specific user
    edges_response = db.table("edges").select("*").eq("telegram_id", telegram_id).execute()
    edges_data = edges_response.data
    
    if not edges_data:
        return []

    # 2. Build the Directed Graph in memory
    G = nx.DiGraph()
    for edge in edges_data:
        G.add_edge(
            edge['source_entity_name'], 
            edge['target_entity_name'], 
            relationship=edge['relationship']
        )

    # 3. Find entities in the query that match our graph nodes
    query_words = set(query_text.lower().split())
    relevant_nodes = [node for node in G.nodes() if node in query_words or any(word in node for word in query_words)]
    
    # 4. Extract relationships for those specific nodes (1st degree connections)
    graph_context = []
    for node in relevant_nodes:
        # Get things this node points to
        for successor in G.successors(node):
            rel = G.edges[node, successor]['relationship']
            graph_context.append(f"{node.title()} {rel} {successor.title()}")
            
        # Get things that point to this node
        for predecessor in G.predecessors(node):
            rel = G.edges[predecessor, node]['relationship']
            graph_context.append(f"{predecessor.title()} {rel} {node.title()}")

    # Return unique relationships
    return list(set(graph_context))