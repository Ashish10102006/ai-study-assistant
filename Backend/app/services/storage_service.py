import os
import sqlite3
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.config.settings import get_settings
from app.services.supabase_client import get_supabase_admin

logger = logging.getLogger("ai_study_assistant.storage")


class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.db_path = Path(self.settings.UPLOAD_DIR).parent / "study_assistant.db"
        self._init_sqlite()

    def _init_sqlite(self):
        """Initializes local SQLite schema to mirror Supabase tables for resilient fallback."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE,
                full_name TEXT,
                email TEXT,
                college TEXT,
                course TEXT,
                year TEXT,
                city TEXT,
                state TEXT,
                country TEXT,
                profile_image TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                subject TEXT,
                topic TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                source_metadata TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_documents (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                file_name TEXT,
                file_type TEXT,
                file_size INTEGER,
                storage_path TEXT,
                processing_status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                chunk_index INTEGER,
                content TEXT,
                metadata TEXT,
                embedding TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("PRAGMA table_info(document_chunks)")
        chunk_cols = [row[1] for row in cursor.fetchall()]
        if "embedding" not in chunk_cols:
            try:
                cursor.execute("ALTER TABLE document_chunks ADD COLUMN embedding TEXT")
            except Exception:
                pass
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_resources (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                url TEXT,
                source TEXT,
                description TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_notes (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                topic TEXT,
                subject TEXT,
                content TEXT,
                document_id TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_notes_user ON saved_notes(user_id)")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interests (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                interest TEXT,
                created_at TEXT,
                UNIQUE(user_id, interest)
            )
        """)
        conn.commit()
        conn.close()

    # ==========================================================
    # CONVERSATIONS & MESSAGES
    # ==========================================================
    def create_conversation(self, user_id: str, title: str, subject: str = "Computer Science", topic: str = "") -> Dict[str, Any]:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()

        if sb:
            try:
                res = sb.table("conversations").insert({
                    "id": conv_id,
                    "user_id": user_id,
                    "title": title,
                    "subject": subject,
                    "topic": topic,
                    "created_at": now,
                    "updated_at": now
                }).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.info(f"Supabase conversations insert notice: {e}. Writing to local database.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT INTO conversations (id, user_id, title, subject, topic, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (conv_id, user_id, title, subject, topic, now, now))
        conn.commit()
        conn.close()

        return {
            "id": conv_id,
            "user_id": user_id,
            "title": title,
            "subject": subject,
            "topic": topic,
            "created_at": now,
            "updated_at": now
        }

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("conversations").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.info(f"Supabase conversations list notice: {e}. Reading from local database.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows

    def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("conversations").select("*").eq("id", conversation_id).eq("user_id", user_id).execute()
                if res.data:
                    conv = res.data[0]
                    # Fetch messages
                    msg_res = sb.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
                    conv["messages"] = msg_res.data or []
                    return conv
            except Exception as e:
                logger.info(f"Supabase get_conversation notice: {e}. Reading from local database.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
        row = c.fetchone()
        if not row:
            conn.close()
            return None

        conv = dict(row)
        c.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
        msg_rows = []
        for m in c.fetchall():
            item = dict(m)
            if item.get("source_metadata") and isinstance(item["source_metadata"], str):
                try:
                    item["source_metadata"] = json.loads(item["source_metadata"])
                except Exception:
                    item["source_metadata"] = {}
            msg_rows.append(item)
        conv["messages"] = msg_rows
        conn.close()
        return conv

    def update_conversation(self, conversation_id: str, user_id: str, title: Optional[str] = None, subject: Optional[str] = None, topic: Optional[str] = None) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()
        updates = {"updated_at": now}
        if title: updates["title"] = title
        if subject: updates["subject"] = subject
        if topic: updates["topic"] = topic

        if sb:
            try:
                res = sb.table("conversations").update(updates).eq("id", conversation_id).eq("user_id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.info(f"Supabase update_conversation notice: {e}.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        set_clauses = ["updated_at = ?"]
        params = [now]
        if title:
            set_clauses.append("title = ?")
            params.append(title)
        if subject:
            set_clauses.append("subject = ?")
            params.append(subject)
        if topic:
            set_clauses.append("topic = ?")
            params.append(topic)
        params.extend([conversation_id, user_id])

        c.execute(f"UPDATE conversations SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?", tuple(params))
        conn.commit()
        conn.close()
        return self.get_conversation(conversation_id, user_id)

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        sb = get_supabase_admin()
        if sb:
            try:
                sb.table("messages").delete().eq("conversation_id", conversation_id).execute()
                sb.table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()
            except Exception as e:
                logger.info(f"Supabase delete_conversation notice: {e}.")

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        c.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))
        conn.commit()
        conn.close()
        return True

    def add_message(self, conversation_id: str, user_id: str, role: str, content: str, source_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        source_metadata = source_metadata or {}
        sb = get_supabase_admin()

        if sb:
            try:
                res = sb.table("messages").insert({
                    "id": msg_id,
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "source_metadata": source_metadata,
                    "created_at": now
                }).execute()
                # Touch conversation updated_at
                sb.table("conversations").update({"updated_at": now}).eq("id", conversation_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.info(f"Supabase add_message notice: {e}.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT INTO messages (id, conversation_id, user_id, role, content, source_metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (msg_id, conversation_id, user_id, role, content, json.dumps(source_metadata), now))
        c.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))
        conn.commit()
        conn.close()

        return {
            "id": msg_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "source_metadata": source_metadata,
            "created_at": now
        }

    # ==========================================================
    # DOCUMENTS & CHUNKS
    # ==========================================================
    def save_document(self, user_id: str, file_name: str, file_type: str, file_size: int, storage_path: str) -> Dict[str, Any]:
        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()

        if sb:
            try:
                res = sb.table("uploaded_documents").insert({
                    "id": doc_id,
                    "user_id": user_id,
                    "file_name": file_name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "storage_path": storage_path,
                    "processing_status": "PROCESSING",
                    "created_at": now,
                    "updated_at": now
                }).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.info(f"Supabase save_document notice: {e}.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT INTO uploaded_documents (id, user_id, file_name, file_type, file_size, storage_path, processing_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'PROCESSING', ?, ?)
        """, (doc_id, user_id, file_name, file_type, file_size, storage_path, now, now))
        conn.commit()
        conn.close()

        return {
            "id": doc_id,
            "user_id": user_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "storage_path": storage_path,
            "processing_status": "PROCESSING",
            "created_at": now,
            "updated_at": now
        }

    def update_document_status(self, document_id: str, status: str):
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()
        if sb:
            try:
                sb.table("uploaded_documents").update({"processing_status": status, "updated_at": now}).eq("id", document_id).execute()
            except Exception:
                pass

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("UPDATE uploaded_documents SET processing_status = ?, updated_at = ? WHERE id = ?", (status, now, document_id))
        conn.commit()
        conn.close()

    def save_document_chunks(self, document_id: str, chunks: List[Dict[str, Any]]):
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()
        if sb and chunks:
            try:
                records = []
                for idx, ch in enumerate(chunks):
                    rec = {
                        "id": str(uuid.uuid4()),
                        "document_id": document_id,
                        "chunk_index": idx,
                        "content": ch["content"],
                        "metadata": ch.get("metadata", {}),
                        "created_at": now
                    }
                    if "embedding" in ch and ch["embedding"]:
                        rec["embedding"] = ch["embedding"]
                    records.append(rec)
                sb.table("document_chunks").insert(records).execute()
            except Exception as e:
                logger.info(f"Supabase chunks insert notice: {e}.")

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        for idx, ch in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            meta = json.dumps(ch.get("metadata", {}))
            emb = ch.get("embedding")
            emb_str = json.dumps(emb) if emb is not None else None
            c.execute("""
                INSERT INTO document_chunks (id, document_id, chunk_index, content, metadata, embedding, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chunk_id, document_id, idx, ch["content"], meta, emb_str, now))
        conn.commit()
        conn.close()

    def list_documents(self, user_id: str) -> List[Dict[str, Any]]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("uploaded_documents").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                if res.data is not None:
                    docs = res.data
                    for d in docs:
                        count_res = sb.table("document_chunks").select("id", count="exact").eq("document_id", d["id"]).execute()
                        d["chunks_count"] = count_res.count if count_res else 0
                    return docs
            except Exception as e:
                logger.info(f"Supabase list_documents notice: {e}.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM uploaded_documents WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        docs = [dict(r) for r in c.fetchall()]
        for d in docs:
            c.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = ?", (d["id"],))
            d["chunks_count"] = c.fetchone()[0]
        conn.close()
        return docs

    def get_document(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("uploaded_documents").select("*").eq("id", document_id).eq("user_id", user_id).execute()
                if res.data:
                    doc = res.data[0]
                    chunks_res = sb.table("document_chunks").select("*").eq("document_id", document_id).order("chunk_index", desc=False).execute()
                    doc["preview_chunks"] = chunks_res.data or []
                    doc["chunks_count"] = len(doc["preview_chunks"])
                    return doc
            except Exception as e:
                logger.info(f"Supabase get_document notice: {e}.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM uploaded_documents WHERE id = ? AND user_id = ?", (document_id, user_id))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        doc = dict(row)
        c.execute("SELECT * FROM document_chunks WHERE document_id = ? ORDER BY chunk_index ASC", (document_id,))
        chunks = []
        for cr in c.fetchall():
            ch = dict(cr)
            if ch.get("metadata") and isinstance(ch["metadata"], str):
                try:
                    ch["metadata"] = json.loads(ch["metadata"])
                except Exception:
                    ch["metadata"] = {}
            chunks.append(ch)
        doc["preview_chunks"] = chunks
        doc["chunks_count"] = len(chunks)
        conn.close()
        return doc

    def delete_document(self, document_id: str, user_id: str) -> bool:
        sb = get_supabase_admin()
        if sb:
            try:
                sb.table("document_chunks").delete().eq("document_id", document_id).execute()
                sb.table("uploaded_documents").delete().eq("id", document_id).eq("user_id", user_id).execute()
            except Exception:
                pass

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))
        c.execute("DELETE FROM uploaded_documents WHERE id = ? AND user_id = ?", (document_id, user_id))
        conn.commit()
        conn.close()
        return True

    def get_raw_chunks_with_embeddings(self, document_id: str) -> List[Dict[str, Any]]:
        """Returns all chunks for a document including embeddings and structured metadata."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT id, document_id, chunk_index, content, metadata, embedding, created_at
            FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC
        """, (document_id,))
        rows = c.fetchall()
        conn.close()
        if rows:
            chunks = []
            for r in rows:
                ch = dict(r)
                if ch.get("metadata") and isinstance(ch["metadata"], str):
                    try:
                        ch["metadata"] = json.loads(ch["metadata"])
                    except Exception:
                        ch["metadata"] = {}
                chunks.append(ch)
            return chunks

        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("document_chunks").select("*").eq("document_id", document_id).order("chunk_index", desc=False).execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.info(f"Supabase get_raw_chunks notice: {e}")
        return []

    def get_document_chunks_for_context(self, document_id: str, query: str = "", limit: int = 6) -> List[str]:
        """Retrieves most relevant document chunks based on keywords or chunk index."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT content FROM document_chunks WHERE document_id = ? ORDER BY chunk_index ASC LIMIT ?", (document_id, limit))
        rows = c.fetchall()
        conn.close()
        if rows:
            return [r["content"] for r in rows]

        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("document_chunks").select("content").eq("document_id", document_id).order("chunk_index", desc=False).limit(limit).execute()
                if res.data:
                    return [r["content"] for r in res.data]
            except Exception:
                pass
        return []

    # ==========================================================
    # SAVED RESOURCES
    # ==========================================================
    def save_resource(self, user_id: str, title: str, url: str, source: str, description: Optional[str] = None) -> Dict[str, Any]:
        res_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("saved_resources").insert({
                    "id": res_id,
                    "user_id": user_id,
                    "title": title,
                    "url": url,
                    "source": source,
                    "description": description or "",
                    "created_at": now
                }).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.info(f"Supabase save_resource notice: {e}.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT INTO saved_resources (id, user_id, title, url, source, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (res_id, user_id, title, url, source, description or "", now))
        conn.commit()
        conn.close()

        return {
            "id": res_id,
            "user_id": user_id,
            "title": title,
            "url": url,
            "source": source,
            "description": description,
            "created_at": now
        }

    def list_saved_resources(self, user_id: str) -> List[Dict[str, Any]]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("saved_resources").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.info(f"Supabase list_saved_resources notice: {e}.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM saved_resources WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def delete_saved_resource(self, resource_id: str, user_id: str) -> bool:
        sb = get_supabase_admin()
        if sb:
            try:
                sb.table("saved_resources").delete().eq("id", resource_id).eq("user_id", user_id).execute()
            except Exception:
                pass

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("DELETE FROM saved_resources WHERE id = ? AND user_id = ?", (resource_id, user_id))
        conn.commit()
        conn.close()
        return True

    # ==========================================================
    # PROFILES & INTERESTS
    # ==========================================================
    def get_or_create_profile(
        self,
        user_id: str,
        email: str = "",
        full_name: Optional[str] = None,
        profile_image: Optional[str] = None
    ) -> Dict[str, Any]:
        sb = get_supabase_admin()
        clean_name = (full_name.strip() if full_name else None) or (email.split("@")[0].title() if email else "Student Scholar")

        if sb:
            try:
                res = sb.table("profiles").select("*").eq("user_id", user_id).execute()
                if res.data:
                    prof = res.data[0]
                    # Fetch interests
                    int_res = sb.table("user_interests").select("interest").eq("user_id", user_id).execute()
                    prof["interests"] = [i["interest"] for i in int_res.data] if int_res.data else []
                    return prof
                else:
                    # Create new profile in Supabase
                    prof_id = str(uuid.uuid4())
                    now = datetime.now(timezone.utc).isoformat()
                    insert_res = sb.table("profiles").insert({
                        "id": prof_id,
                        "user_id": user_id,
                        "full_name": clean_name,
                        "email": email,
                        "college": "Engineering & Science College",
                        "course": "Computer Science",
                        "year": "3rd Year",
                        "profile_image": profile_image,
                        "created_at": now,
                        "updated_at": now
                    }).execute()
                    if insert_res.data:
                        prof = insert_res.data[0]
                        prof["interests"] = ["Data Structures", "Algorithms", "Operating Systems", "Artificial Intelligence"]
                        return prof
            except Exception as e:
                logger.info(f"Supabase profile operation notice: {e}. Falling back to local storage.")

        # SQLite Fallback
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            prof = dict(row)
            c.execute("SELECT interest FROM user_interests WHERE user_id = ?", (user_id,))
            prof["interests"] = [r["interest"] for r in c.fetchall()]
            conn.close()
            return prof

        # Create new
        prof_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        c.execute("""
            INSERT INTO profiles (id, user_id, full_name, email, college, course, year, profile_image, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'Engineering & Science College', 'Computer Science', '3rd Year', ?, ?, ?)
        """, (prof_id, user_id, clean_name, email, profile_image, now, now))
        conn.commit()
        conn.close()

        return {
            "id": prof_id,
            "user_id": user_id,
            "full_name": clean_name,
            "email": email,
            "college": "Engineering & Science College",
            "course": "Computer Science",
            "year": "3rd Year",
            "profile_image": profile_image,
            "interests": ["Data Structures", "Algorithms", "Operating Systems", "Artificial Intelligence"],
            "created_at": now,
            "updated_at": now
        }

    def update_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()
        interests = data.pop("interests", None)
        data["updated_at"] = now

        if sb:
            try:
                sb.table("profiles").update(data).eq("user_id", user_id).execute()
                if interests is not None:
                    sb.table("user_interests").delete().eq("user_id", user_id).execute()
                    if interests:
                        sb.table("user_interests").insert([{"id": str(uuid.uuid4()), "user_id": user_id, "interest": item} for item in interests]).execute()
            except Exception:
                pass

        # SQLite
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        set_parts = [f"{k} = ?" for k in data.keys()]
        params = list(data.values())
        params.append(user_id)
        c.execute(f"UPDATE profiles SET {', '.join(set_parts)} WHERE user_id = ?", tuple(params))

        if interests is not None:
            c.execute("DELETE FROM user_interests WHERE user_id = ?", (user_id,))
            for item in interests:
                c.execute("INSERT OR IGNORE INTO user_interests (id, user_id, interest, created_at) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), user_id, item, now))

        conn.commit()
        conn.close()
        return self.get_or_create_profile(user_id)

    # ==========================================================
    # SAVED NOTES PERSISTENCE & USER ISOLATION
    # ==========================================================
    def save_note(
        self,
        user_id: str,
        topic: str,
        content: str,
        subject: Optional[str] = "Computer Science",
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        note_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        sb = get_supabase_admin()

        if sb:
            try:
                res = sb.table("saved_notes").insert({
                    "id": note_id,
                    "user_id": user_id,
                    "topic": topic,
                    "subject": subject,
                    "content": content,
                    "document_id": document_id,
                    "created_at": now,
                    "updated_at": now
                }).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.info(f"Supabase saved_notes notice: {e}. Writing to local database.")

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            INSERT INTO saved_notes (id, user_id, topic, subject, content, document_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (note_id, user_id, topic, subject, content, document_id, now, now))
        conn.commit()
        conn.close()

        return {
            "id": note_id,
            "user_id": user_id,
            "topic": topic,
            "subject": subject,
            "content": content,
            "document_id": document_id,
            "created_at": now,
            "updated_at": now
        }

    def list_saved_notes(self, user_id: str) -> List[Dict[str, Any]]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("saved_notes").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.info(f"Supabase list_saved_notes notice: {e}. Reading from local database.")

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT id, user_id, topic, subject, content, document_id, created_at, updated_at FROM saved_notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = c.fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "user_id": r[1],
                "topic": r[2],
                "subject": r[3],
                "content": r[4],
                "document_id": r[5],
                "created_at": r[6],
                "updated_at": r[7]
            } for r in rows
        ]

    def get_saved_note(self, note_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("saved_notes").select("*").eq("id", note_id).eq("user_id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception:
                pass

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT id, user_id, topic, subject, content, document_id, created_at, updated_at FROM saved_notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "user_id": row[1],
            "topic": row[2],
            "subject": row[3],
            "content": row[4],
            "document_id": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }

    def update_saved_note(
        self,
        note_id: str,
        user_id: str,
        content: Optional[str] = None,
        topic: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        fields = {}
        if content is not None:
            fields["content"] = content
        if topic is not None:
            fields["topic"] = topic
        if subject is not None:
            fields["subject"] = subject

        if not fields:
            return self.get_saved_note(note_id, user_id)

        fields["updated_at"] = now
        sb = get_supabase_admin()
        if sb:
            try:
                sb.table("saved_notes").update(fields).eq("id", note_id).eq("user_id", user_id).execute()
            except Exception:
                pass

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        params = list(fields.values()) + [note_id, user_id]
        c.execute(f"UPDATE saved_notes SET {set_clause} WHERE id = ? AND user_id = ?", tuple(params))
        conn.commit()
        conn.close()

        return self.get_saved_note(note_id, user_id)

    def delete_saved_note(self, note_id: str, user_id: str) -> bool:
        sb = get_supabase_admin()
        if sb:
            try:
                sb.table("saved_notes").delete().eq("id", note_id).eq("user_id", user_id).execute()
            except Exception:
                pass

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("DELETE FROM saved_notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        affected = c.rowcount
        conn.commit()
        conn.close()

        return affected > 0


_storage_instance: Optional[StorageService] = None

def get_storage_service() -> StorageService:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageService()
    return _storage_instance
