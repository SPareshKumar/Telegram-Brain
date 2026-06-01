-- 02_match_notes_rpc.sql
-- Function to perform semantic vector search over user notes using cosine distance.
-- This aligns with the 'vector_cosine_ops' index created in 01_initial_schema.sql.

CREATE OR REPLACE FUNCTION match_notes(
    query_embedding vector(768),
    match_threshold float,
    match_count int,
    p_telegram_id bigint
)
RETURNS TABLE (
    id uuid,
    content text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.content,
        1 - (ne.embedding <=> query_embedding) AS similarity
    FROM
        notes n
    JOIN
        note_embeddings ne ON n.id = ne.id
    WHERE
        n.telegram_id = p_telegram_id
        -- Calculate similarity as (1 - cosine_distance). 
        -- Ensures higher similarity score is better and properly filters by threshold.
        AND 1 - (ne.embedding <=> query_embedding) > match_threshold
    ORDER BY
        -- Order by nearest neighbor (lowest distance) first
        ne.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;
