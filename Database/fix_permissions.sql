-- ==========================================================
-- AI STUDY ASSISTANT - FIX PERMISSIONS SCRIPT FOR SUPABASE
-- Run this in Supabase Dashboard -> SQL Editor -> New Query -> Run
-- ==========================================================

-- 1. Ensure public schema usage is granted to all Supabase roles
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;

-- 2. Grant full table, sequence, and function privileges to service_role (used by the Backend API)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT ALL PRIVILEGES ON ALL ROUTINES IN SCHEMA public TO postgres, service_role;

-- 3. Grant CRUD privileges to authenticated and guest anon roles (strictly filtered by Row Level Security)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated, anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated, anon;

-- 4. Ensure future tables automatically inherit these privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO postgres, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated, anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO authenticated, anon;

-- Verification check: show table privileges for service_role
SELECT table_name, privilege_type 
FROM information_schema.role_table_grants 
WHERE grantee = 'service_role' AND table_schema = 'public';
