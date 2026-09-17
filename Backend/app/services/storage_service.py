import os
import sqlite3
import json
import uuid
import logging
from datetime import datetime
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
                created_at TEXT
            )
        """)
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
        now = datetime.utcnow().isoformat()
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
        now = datetime.utcnow().isoformat()
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
        now = datetime.utcnow().isoformat()
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
        now = datetime.utcnow().isoformat()
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
        now = datetime.utcnow().isoformat()
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
        now = datetime.utcnow().isoformat()
        sb = get_supabase_admin()
        if sb and chunks:
            try:
                records = [{
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "chunk_index": idx,
                    "content": ch["content"],
                    "metadata": ch.get("metadata", {}),
                    "created_at": now
                } for idx, ch in enumerate(chunks)]
                sb.table("document_chunks").insert(records).execute()
            except Exception as e:
                logger.info(f"Supabase chunks insert notice: {e}.")

        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        for idx, ch in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            meta = json.dumps(ch.get("metadata", {}))
            c.execute("""
                INSERT INTO document_chunks (id, document_id, chunk_index, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chunk_id, document_id, idx, ch["content"], meta, now))
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
        now = datetime.utcnow().isoformat()
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
    def get_or_create_profile(self, user_id: str, email: str = "") -> Dict[str, Any]:
        sb = get_supabase_admin()
        if sb:
            try:
                res = sb.table("profiles").select("*").eq("user_id", user_id).execute()
                if res.data:
                    prof = res.data[0]
                    # Fetch interests
                    int_res = sb.table("user_interests").select("interest").eq("user_id", user_id).execute()
                    prof["interests"] = [i["interest"] for i in int_res.data] if int_res.data else []
                    return prof
            except Exception:
                pass

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
        now = datetime.utcnow().isoformat()
        c.execute("""
            INSERT INTO profiles (id, user_id, full_name, email, college, course, year, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'Engineering & Science College', 'Computer Science', '3rd Year', ?, ?)
        """, (prof_id, user_id, email.split("@")[0].title() if email else "Student Scholar", email, now, now))
        conn.commit()
        conn.close()

        return {
            "id": prof_id,
            "user_id": user_id,
            "full_name": email.split("@")[0].title() if email else "Student Scholar",
            "email": email,
            "college": "Engineering & Science College",
            "course": "Computer Science",
            "year": "3rd Year",
            "interests": ["Data Structures", "Algorithms", "Operating Systems", "Artificial Intelligence"],
            "created_at": now,
            "updated_at": now
        }

    def update_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
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


_storage_instance: Optional[StorageService] = None

def get_storage_service() -> StorageService:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageService()
    return _storage_instance
