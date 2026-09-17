-- ==========================================================
-- AI STUDY ASSISTANT - PRODUCTION SUPABASE DATABASE SCHEMA
-- Compatible with both Authenticated Users and Device Guest Scholars
-- ==========================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================================
-- 1. PROFILES TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL UNIQUE,
    full_name TEXT,
    email TEXT,
    college TEXT,
    course TEXT,
    year TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    profile_image TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles(user_id);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to profiles" ON public.profiles;
CREATE POLICY "Allow service role full access to profiles"
    ON public.profiles FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view their own profile" ON public.profiles;
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;
CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid()::text = user_id);

-- ==========================================================
-- 2. CONVERSATIONS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    subject TEXT,
    topic TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON public.conversations(updated_at DESC);

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to conversations" ON public.conversations;
CREATE POLICY "Allow service role full access to conversations"
    ON public.conversations FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view their own conversations" ON public.conversations;
CREATE POLICY "Users can view their own conversations"
    ON public.conversations FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert their own conversations" ON public.conversations;
CREATE POLICY "Users can insert their own conversations"
    ON public.conversations FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update their own conversations" ON public.conversations;
CREATE POLICY "Users can update their own conversations"
    ON public.conversations FOR UPDATE
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete their own conversations" ON public.conversations;
CREATE POLICY "Users can delete their own conversations"
    ON public.conversations FOR DELETE
    USING (auth.uid()::text = user_id);

-- ==========================================================
-- 3. MESSAGES TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    conversation_id TEXT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('USER', 'ASSISTANT', 'SYSTEM')),
    content TEXT NOT NULL,
    source_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at ASC);

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to messages" ON public.messages;
CREATE POLICY "Allow service role full access to messages"
    ON public.messages FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view messages from their conversations" ON public.messages;
CREATE POLICY "Users can view messages from their conversations"
    ON public.messages FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert messages into their conversations" ON public.messages;
CREATE POLICY "Users can insert messages into their conversations"
    ON public.messages FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete their own messages" ON public.messages;
CREATE POLICY "Users can delete their own messages"
    ON public.messages FOR DELETE
    USING (auth.uid()::text = user_id);

-- ==========================================================
-- 4. UPLOADED DOCUMENTS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.uploaded_documents (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    processing_status TEXT NOT NULL CHECK (processing_status IN ('UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED')) DEFAULT 'UPLOADED',
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_uploaded_documents_user_id ON public.uploaded_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_documents_created_at ON public.uploaded_documents(created_at DESC);

ALTER TABLE public.uploaded_documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to uploaded_documents" ON public.uploaded_documents;
CREATE POLICY "Allow service role full access to uploaded_documents"
    ON public.uploaded_documents FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view their own documents" ON public.uploaded_documents;
CREATE POLICY "Users can view their own documents"
    ON public.uploaded_documents FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert their own documents" ON public.uploaded_documents;
CREATE POLICY "Users can insert their own documents"
    ON public.uploaded_documents FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update their own documents" ON public.uploaded_documents;
CREATE POLICY "Users can update their own documents"
    ON public.uploaded_documents FOR UPDATE
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete their own documents" ON public.uploaded_documents;
CREATE POLICY "Users can delete their own documents"
    ON public.uploaded_documents FOR DELETE
    USING (auth.uid()::text = user_id);

-- ==========================================================
-- 5. DOCUMENT CHUNKS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.document_chunks (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    document_id TEXT NOT NULL REFERENCES public.uploaded_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON public.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_index ON public.document_chunks(document_id, chunk_index);

ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to document_chunks" ON public.document_chunks;
CREATE POLICY "Allow service role full access to document_chunks"
    ON public.document_chunks FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view chunks of their documents" ON public.document_chunks;
CREATE POLICY "Users can view chunks of their documents"
    ON public.document_chunks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.uploaded_documents d
            WHERE d.id = document_chunks.document_id AND d.user_id = auth.uid()::text
        )
    );

-- ==========================================================
-- 6. SAVED RESOURCES TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.saved_resources (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saved_resources_user_id ON public.saved_resources(user_id);

ALTER TABLE public.saved_resources ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to saved_resources" ON public.saved_resources;
CREATE POLICY "Allow service role full access to saved_resources"
    ON public.saved_resources FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view their saved resources" ON public.saved_resources;
CREATE POLICY "Users can view their saved resources"
    ON public.saved_resources FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert saved resources" ON public.saved_resources;
CREATE POLICY "Users can insert saved resources"
    ON public.saved_resources FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete their saved resources" ON public.saved_resources;
CREATE POLICY "Users can delete their saved resources"
    ON public.saved_resources FOR DELETE
    USING (auth.uid()::text = user_id);

-- ==========================================================
-- 7. STUDY SESSIONS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.study_sessions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    subject TEXT,
    session_type TEXT NOT NULL,
    duration_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON public.study_sessions(user_id);

ALTER TABLE public.study_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to study_sessions" ON public.study_sessions;
CREATE POLICY "Allow service role full access to study_sessions"
    ON public.study_sessions FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view their study sessions" ON public.study_sessions;
CREATE POLICY "Users can view their study sessions"
    ON public.study_sessions FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert their study sessions" ON public.study_sessions;
CREATE POLICY "Users can insert their study sessions"
    ON public.study_sessions FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- ==========================================================
-- 8. USER INTERESTS TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.user_interests (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    interest TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE(user_id, interest)
);

CREATE INDEX IF NOT EXISTS idx_user_interests_user_id ON public.user_interests(user_id);

ALTER TABLE public.user_interests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to user_interests" ON public.user_interests;
CREATE POLICY "Allow service role full access to user_interests"
    ON public.user_interests FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view their own interests" ON public.user_interests;
CREATE POLICY "Users can view their own interests"
    ON public.user_interests FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert their own interests" ON public.user_interests;
CREATE POLICY "Users can insert their own interests"
    ON public.user_interests FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete their own interests" ON public.user_interests;
CREATE POLICY "Users can delete their own interests"
    ON public.user_interests FOR DELETE
    USING (auth.uid()::text = user_id);

-- ==========================================================
-- 9. SEARCH HISTORY TABLE
-- ==========================================================
CREATE TABLE IF NOT EXISTS public.search_history (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON public.search_history(user_id);

ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow service role full access to search_history" ON public.search_history;
CREATE POLICY "Allow service role full access to search_history"
    ON public.search_history FOR ALL
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Users can view their search history" ON public.search_history;
CREATE POLICY "Users can view their search history"
    ON public.search_history FOR SELECT
    USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can insert search history" ON public.search_history;
CREATE POLICY "Users can insert search history"
    ON public.search_history FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- ==========================================================
-- 10. AUTOMATIC PROFILE CREATION TRIGGER (FOR REGISTERED USERS)
-- ==========================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (user_id, full_name, email)
    VALUES (
        NEW.id::text,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        NEW.email
    )
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==========================================================
-- 11. AUTOMATIC UPDATED_AT TRIGGER
-- ==========================================================
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_profiles_updated_at ON public.profiles;
CREATE TRIGGER set_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS set_conversations_updated_at ON public.conversations;
CREATE TRIGGER set_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS set_documents_updated_at ON public.uploaded_documents;
CREATE TRIGGER set_documents_updated_at
    BEFORE UPDATE ON public.uploaded_documents
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ==========================================================
-- 12. ROLE PERMISSIONS & GRANTS (REQUIRED FOR SUPABASE API & SERVICE ROLE)
-- ==========================================================
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT ALL PRIVILEGES ON ALL ROUTINES IN SCHEMA public TO postgres, service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated, anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated, anon;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO postgres, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated, anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO authenticated, anon;

