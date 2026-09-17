# AI STUDY ASSISTANT - Database Setup Guide

This directory contains the PostgreSQL schema and migrations for **AI STUDY ASSISTANT** powered by **Supabase**.

## Tables

| Table Name | Description | RLS Protected |
|---|---|---|
| `profiles` | Student profile (college, course, year, location, avatar) | Yes |
| `conversations` | Conversation threads (subject, topic, timestamp) | Yes |
| `messages` | Chat messages with role (`USER`, `ASSISTANT`, `SYSTEM`) and metadata | Yes |
| `uploaded_documents` | File metadata, storage path, and processing status | Yes |
| `document_chunks` | Extracted text chunks with index and metadata for grounded Q&A | Yes |
| `saved_resources` | Curated academic links bookmarked by students | Yes |
| `study_sessions` | Track study duration and topic coverage | Yes |
| `user_interests` | Academic subject interests and tags | Yes |
| `search_history` | History of student academic searches | Yes |

## Quick Setup on Supabase

1. Open your [Supabase Dashboard](https://supabase.com/dashboard).
2. Navigate to your project.
3. In the left sidebar, click **SQL Editor**.
4. Click **New Query**.
5. Copy and paste the contents of `schema.sql` into the editor.
6. Click **Run** (or Ctrl+Enter).

All tables, indexes, Row Level Security policies, and triggers will be created instantly.
