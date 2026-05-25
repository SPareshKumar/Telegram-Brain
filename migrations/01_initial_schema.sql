-- 1. Enable the pgvector extension for AI semantic search
create extension if not exists vector;

-- 2. CREATE TABLES
create table users (
    telegram_id bigint primary key,
    username text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table notes (
    id uuid default gen_random_uuid() primary key,
    telegram_id bigint references users(telegram_id) on delete cascade,
    content text not null,
    cleaned_content text, 
    media_type text default 'text', 
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table note_embeddings (
    id uuid primary key references notes(id) on delete cascade,
    telegram_id bigint references users(telegram_id) on delete cascade,
    embedding vector(768),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table secure_vault (
    id uuid default gen_random_uuid() primary key,
    telegram_id bigint references users(telegram_id) on delete cascade,
    secret_type text check (secret_type in ('password', 'api_key', 'account_no')),
    encrypted_value text not null, 
    associated_label text not null, 
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table graph_edges (
    id uuid default gen_random_uuid() primary key,
    telegram_id bigint references users(telegram_id) on delete cascade,
    source_node text not null,
    relationship text not null, 
    target_node text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. PERFORMANCE TUNING (Indexes)
create index idx_notes_user on notes(telegram_id);
create index idx_vault_user on secure_vault(telegram_id);
create index idx_graph_user on graph_edges(telegram_id);
create index idx_vector_cos on note_embeddings using hnsw (embedding vector_cosine_ops);

-- 4. ROW LEVEL SECURITY (RLS)
-- Lock down all tables to prevent public frontend access
alter table users enable row level security;
alter table notes enable row level security;
alter table note_embeddings enable row level security;
alter table secure_vault enable row level security;
alter table graph_edges enable row level security;

-- Deny public read access explicitly
create policy "Deny public read access" on users for select using (false);
create policy "Deny public read access" on notes for select using (false);
create policy "Deny public read access" on secure_vault for select using (false);