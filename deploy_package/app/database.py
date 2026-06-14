"""
SQLite 数据库管理模块
负责数据库连接、建表和全部 CRUD 操作
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from .config import settings


class Database:
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_admin INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT DEFAULT '',
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename VARCHAR(255) NOT NULL,
                knowledge_base_id INTEGER NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INTEGER DEFAULT 0,
                file_type VARCHAR(20) DEFAULT '',
                chunk_count INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'processing',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                knowledge_base_id INTEGER NOT NULL,
                title VARCHAR(200) DEFAULT '新对话',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role VARCHAR(10) NOT NULL,
                content TEXT NOT NULL,
                sources TEXT DEFAULT NULL,
                feedback VARCHAR(10) DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT DEFAULT '',
                system_prompt TEXT NOT NULL,
                default_top_k INTEGER DEFAULT 4,
                default_temperature REAL DEFAULT 0.3,
                is_default INTEGER DEFAULT 0,
                user_id INTEGER DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action VARCHAR(50) NOT NULL,
                target VARCHAR(100) DEFAULT '',
                detail TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS knowledge_base_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_base_id INTEGER NOT NULL,
                shared_with_user_id INTEGER NOT NULL,
                shared_by_user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (shared_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE(knowledge_base_id, shared_with_user_id)
            );

            CREATE TABLE IF NOT EXISTS knowledge_base_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_base_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                vote_type TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(knowledge_base_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS document_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                user_id INTEGER NOT NULL,
                reason TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                resolve_reason TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS document_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(document_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS knowledge_base_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_base_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(knowledge_base_id, user_id)
            );
        """)

        # 迁移：给旧表加新字段（如果不存在）
        try:
            cursor.execute("ALTER TABLE prompt_templates ADD COLUMN default_top_k INTEGER DEFAULT 4")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE prompt_templates ADD COLUMN default_temperature REAL DEFAULT 0.3")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE knowledge_bases ADD COLUMN visibility TEXT DEFAULT 'private'")
        except Exception:
            pass

        conn.commit()

        # 兼容旧数据库：自动补齐缺失的列和表
        self._migrate_schema(cursor)

        conn.commit()
        conn.close()

    def _migrate_schema(self, cursor):
        """自动迁移旧数据库 schema，补齐缺失的列"""
        try:
            # 检查 users 表是否有 is_admin 列
            cursor.execute("PRAGMA table_info(users)")
            user_cols = {row[1] for row in cursor.fetchall()}
            if "is_admin" not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
                print("[迁移] users 表已添加 is_admin 列")
        except Exception as e:
            print(f"[迁移] users 表迁移: {e}")

        try:
            # 检查 conversations 表是否有 title 列
            cursor.execute("PRAGMA table_info(conversations)")
            conv_cols = {row[1] for row in cursor.fetchall()}
            if "title" not in conv_cols:
                cursor.execute("ALTER TABLE conversations ADD COLUMN title VARCHAR(200) DEFAULT '新对话'")
                print("[迁移] conversations 表已添加 title 列")
        except Exception as e:
            print(f"[迁移] conversations 表迁移: {e}")

        try:
            # 检查 knowledge_base_shares 表是否有 shared_by_user_id 列
            cursor.execute("PRAGMA table_info(knowledge_base_shares)")
            share_cols = {row[1] for row in cursor.fetchall()}
            if "shared_by_user_id" not in share_cols:
                cursor.execute("ALTER TABLE knowledge_base_shares ADD COLUMN shared_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL")
                print("[迁移] knowledge_base_shares 表已添加 shared_by_user_id 列")
        except Exception as e:
            print(f"[迁移] knowledge_base_shares 表迁移: {e}")

        try:
            # 检查 document_reports 表是否有 resolve_reason 列
            cursor.execute("PRAGMA table_info(document_reports)")
            report_cols = {row[1] for row in cursor.fetchall()}
            if "resolve_reason" not in report_cols:
                cursor.execute("ALTER TABLE document_reports ADD COLUMN resolve_reason TEXT DEFAULT ''")
                print("[迁移] document_reports 表已添加 resolve_reason 列")
        except Exception as e:
            print(f"[迁移] document_reports 表迁移: {e}")

        try:
            # 检查 knowledge_bases 表是否有 reject_reason 列
            cursor.execute("PRAGMA table_info(knowledge_bases)")
            kb_cols = {row[1] for row in cursor.fetchall()}
            if "reject_reason" not in kb_cols:
                cursor.execute("ALTER TABLE knowledge_bases ADD COLUMN reject_reason TEXT DEFAULT ''")
                print("[迁移] knowledge_bases 表已添加 reject_reason 列")
        except Exception as e:
            print(f"[迁移] knowledge_bases 表迁移: {e}")

        try:
            # 检查 messages 表是否有 feedback 列
            cursor.execute("PRAGMA table_info(messages)")
            msg_cols = {row[1] for row in cursor.fetchall()}
            if "feedback" not in msg_cols:
                cursor.execute("ALTER TABLE messages ADD COLUMN feedback VARCHAR(10) DEFAULT NULL")
                print("[迁移] messages 表已添加 feedback 列")
        except Exception as e:
            print(f"[迁移] messages 表迁移: {e}")

        try:
            # 检查 documents 表是否有 file_size/file_type 列
            cursor.execute("PRAGMA table_info(documents)")
            doc_cols = {row[1] for row in cursor.fetchall()}
            if "file_size" not in doc_cols:
                cursor.execute("ALTER TABLE documents ADD COLUMN file_size INTEGER DEFAULT 0")
                print("[迁移] documents 表已添加 file_size 列")
            if "file_type" not in doc_cols:
                cursor.execute("ALTER TABLE documents ADD COLUMN file_type VARCHAR(20) DEFAULT ''")
                print("[迁移] documents 表已添加 file_type 列")
        except Exception as e:
            print(f"[迁移] documents 表迁移: {e}")

        try:
            # 检查 prompt_templates 和 operation_logs 表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_templates'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS prompt_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL,
                        description TEXT DEFAULT '',
                        system_prompt TEXT NOT NULL,
                        is_default INTEGER DEFAULT 0,
                        user_id INTEGER DEFAULT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                print("[迁移] 已创建 prompt_templates 表")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operation_logs'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS operation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        target VARCHAR(100) DEFAULT '',
                        detail TEXT DEFAULT '',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                print("[迁移] 已创建 operation_logs 表")
        except Exception as e:
            print(f"[迁移] 新表创建: {e}")

    # ==================== 用户操作 ====================

    def create_user(self, username: str, hashed_password: str, is_admin: bool = False) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, hashed_password, is_admin) VALUES (?, ?, ?)",
            (username, hashed_password, 1 if is_admin else 0)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_user_password(self, user_id: int, hashed_password: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET hashed_password = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()
        conn.close()

    def update_user_admin(self, user_id: int, is_admin: bool):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if is_admin else 0, user_id))
        conn.commit()
        conn.close()

    def get_all_users(self) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_user(self, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

    # ==================== 知识库操作 ====================

    def create_knowledge_base(self, name: str, description: str, user_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO knowledge_bases (name, description, user_id) VALUES (?, ?, ?)",
            (name, description, user_id)
        )
        conn.commit()
        kb_id = cursor.lastrowid
        conn.close()
        return kb_id

    def get_knowledge_bases_by_user(self, user_id: int) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT kb.*,
                   COUNT(DISTINCT d.id) as document_count,
                   COALESCE(SUM(d.chunk_count), 0) as chunk_count
            FROM knowledge_bases kb
            LEFT JOIN documents d ON kb.id = d.knowledge_base_id
            WHERE kb.user_id = ?
            GROUP BY kb.id
            ORDER BY kb.created_at DESC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_knowledge_base_by_id(self, kb_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM knowledge_bases WHERE id = ?", (kb_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_knowledge_base(self, kb_id: int, name: Optional[str] = None, description: Optional[str] = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if updates:
            params.append(kb_id)
            cursor.execute(f"UPDATE knowledge_bases SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        conn.close()

    def delete_knowledge_base(self, kb_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb_id,))
        conn.commit()
        conn.close()

    def get_all_knowledge_bases(self) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT kb.*,
                   u.username,
                   COUNT(DISTINCT d.id) as document_count,
                   COALESCE(SUM(d.chunk_count), 0) as chunk_count
            FROM knowledge_bases kb
            JOIN users u ON kb.user_id = u.id
            LEFT JOIN documents d ON kb.id = d.knowledge_base_id
            GROUP BY kb.id
            ORDER BY kb.created_at DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== 文档操作 ====================

    def create_document(self, filename: str, knowledge_base_id: int, file_path: str,
                        file_size: int = 0, file_type: str = "") -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (filename, knowledge_base_id, file_path, file_size, file_type) VALUES (?, ?, ?, ?, ?)",
            (filename, knowledge_base_id, file_path, file_size, file_type)
        )
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()
        return doc_id

    def update_document_status(self, doc_id: int, status: str, chunk_count: int = 0):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
            (status, chunk_count, doc_id)
        )
        conn.commit()
        conn.close()

    def get_documents_by_kb(self, kb_id: int) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE knowledge_base_id = ? ORDER BY created_at DESC",
            (kb_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_document(self, doc_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()

    # ==================== 对话操作 ====================

    def create_conversation(self, user_id: int, knowledge_base_id: int, title: str = "新对话") -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (user_id, knowledge_base_id, title) VALUES (?, ?, ?)",
            (user_id, knowledge_base_id, title)
        )
        conn.commit()
        conv_id = cursor.lastrowid
        conn.close()
        return conv_id

    def get_conversations_by_user(self, user_id: int, keyword: str = None) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if keyword:
            cursor.execute(
                """
                SELECT c.id, c.created_at, c.knowledge_base_id, c.title,
                       kb.name as knowledge_base_name,
                       COUNT(m.id) as message_count
                FROM conversations c
                JOIN knowledge_bases kb ON c.knowledge_base_id = kb.id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = ? AND c.title LIKE ?
                GROUP BY c.id
                ORDER BY c.created_at DESC
                """,
                (user_id, f"%{keyword}%")
            )
        else:
            cursor.execute(
                """
                SELECT c.id, c.created_at, c.knowledge_base_id, c.title,
                       kb.name as knowledge_base_name,
                       COUNT(m.id) as message_count
                FROM conversations c
                JOIN knowledge_bases kb ON c.knowledge_base_id = kb.id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY c.created_at DESC
                """,
                (user_id,)
            )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_conversation_by_id(self, conv_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, kb.name as knowledge_base_name
            FROM conversations c
            JOIN knowledge_bases kb ON c.knowledge_base_id = kb.id
            WHERE c.id = ?
            """,
            (conv_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_conversation_title(self, conv_id: int, title: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id))
        conn.commit()
        conn.close()

    def delete_conversation(self, conv_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()
        conn.close()

    # ==================== 消息操作 ====================

    def create_message(self, conversation_id: int, role: str, content: str, sources: str = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content, sources) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, sources)
        )
        conn.commit()
        msg_id = cursor.lastrowid
        conn.close()
        return msg_id

    def get_messages_by_conversation(self, conv_id: int) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_message_by_id(self, msg_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_message(self, msg_id: int, content: str, sources: str = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        if sources is not None:
            cursor.execute("UPDATE messages SET content = ?, sources = ? WHERE id = ?", (content, sources, msg_id))
        else:
            cursor.execute("UPDATE messages SET content = ? WHERE id = ?", (content, msg_id))
        conn.commit()
        conn.close()

    def update_message_feedback(self, msg_id: int, feedback: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET feedback = ? WHERE id = ?", (feedback, msg_id))
        conn.commit()
        conn.close()

    # ==================== Prompt 模板操作 ====================

    def create_prompt_template(self, name: str, system_prompt: str, description: str = "",
                               user_id: int = None, is_default: bool = False,
                               default_top_k: int = 4, default_temperature: float = 0.3) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO prompt_templates (name, system_prompt, description, user_id, is_default, default_top_k, default_temperature) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, system_prompt, description, user_id, 1 if is_default else 0, default_top_k, default_temperature)
        )
        conn.commit()
        tmpl_id = cursor.lastrowid
        conn.close()
        return tmpl_id

    def get_prompt_templates(self, user_id: int = None) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                "SELECT * FROM prompt_templates WHERE user_id IS NULL OR user_id = ? ORDER BY is_default DESC, created_at DESC",
                (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM prompt_templates WHERE user_id IS NULL ORDER BY is_default DESC, created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_prompt_template_by_id(self, tmpl_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompt_templates WHERE id = ?", (tmpl_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_prompt_template(self, tmpl_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompt_templates WHERE id = ?", (tmpl_id,))
        conn.commit()
        conn.close()

    def update_prompt_template(self, tmpl_id: int, name: str = None, description: str = None,
                               system_prompt: str = None, default_top_k: int = None, default_temperature: float = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if system_prompt is not None:
            updates.append("system_prompt = ?")
            params.append(system_prompt)
        if default_top_k is not None:
            updates.append("default_top_k = ?")
            params.append(default_top_k)
        if default_temperature is not None:
            updates.append("default_temperature = ?")
            params.append(default_temperature)
        if updates:
            params.append(tmpl_id)
            cursor.execute(f"UPDATE prompt_templates SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        conn.close()

    # ==================== 操作日志 ====================

    def create_log(self, user_id: int, action: str, target: str = "", detail: str = ""):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO operation_logs (user_id, action, target, detail) VALUES (?, ?, ?, ?)",
            (user_id, action, target, detail)
        )
        conn.commit()
        conn.close()

    def get_logs(self, page: int = 1, page_size: int = 20, user_id: int = None) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        offset = (page - 1) * page_size
        if user_id:
            cursor.execute(
                """
                SELECT ol.*, u.username FROM operation_logs ol
                JOIN users u ON ol.user_id = u.id
                WHERE ol.user_id = ?
                ORDER BY ol.created_at DESC LIMIT ? OFFSET ?
                """,
                (user_id, page_size, offset)
            )
        else:
            cursor.execute(
                """
                SELECT ol.*, u.username FROM operation_logs ol
                JOIN users u ON ol.user_id = u.id
                ORDER BY ol.created_at DESC LIMIT ? OFFSET ?
                """,
                (page_size, offset)
            )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== 统计操作 ====================

    def get_user_stats(self, user_id: int) -> Dict:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_bases WHERE user_id = ?", (user_id,))
        kb_count = cursor.fetchone()["cnt"]

        cursor.execute(
            "SELECT COUNT(*) as cnt FROM documents d JOIN knowledge_bases kb ON d.knowledge_base_id = kb.id WHERE kb.user_id = ?",
            (user_id,)
        )
        doc_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM conversations WHERE user_id = ?", (user_id,))
        conv_count = cursor.fetchone()["cnt"]

        cursor.execute(
            "SELECT COUNT(*) as cnt FROM messages m JOIN conversations c ON m.conversation_id = c.id WHERE c.user_id = ?",
            (user_id,)
        )
        msg_count = cursor.fetchone()["cnt"]

        conn.close()
        return {
            "knowledge_base_count": kb_count,
            "document_count": doc_count,
            "conversation_count": conv_count,
            "message_count": msg_count,
        }

    def get_system_stats(self) -> Dict:
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}
        for table in ["users", "knowledge_bases", "documents", "conversations", "messages"]:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            stats[f"total_{table}"] = cursor.fetchone()["cnt"]

        # 统计公共/私有知识库
        cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_bases WHERE visibility = 'public'")
        stats["public_knowledge_bases"] = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_bases WHERE visibility = 'private' OR visibility IS NULL")
        stats["private_knowledge_bases"] = cursor.fetchone()["cnt"]

        conn.close()
        return stats

    # ==================== 分享操作 ====================

    def share_knowledge_base(self, kb_id: int, user_id: int, shared_by_user_id: int = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO knowledge_base_shares (knowledge_base_id, shared_with_user_id, shared_by_user_id) VALUES (?, ?, ?)",
                (kb_id, user_id, shared_by_user_id)
            )
            conn.commit()
        except Exception as e:
            print(f"[错误] share_knowledge_base: {e}")
            conn.rollback()
        finally:
            conn.close()

    def unshare_knowledge_base(self, kb_id: int, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM knowledge_base_shares WHERE knowledge_base_id = ? AND shared_with_user_id = ?",
            (kb_id, user_id)
        )
        conn.commit()
        conn.close()

    def get_shared_users(self, kb_id: int) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT s.shared_with_user_id, u.username, s.shared_by_user_id,
                   bu.username as shared_by_username
                FROM knowledge_base_shares s
                JOIN users u ON s.shared_with_user_id = u.id
                LEFT JOIN users bu ON s.shared_by_user_id = bu.id
                WHERE s.knowledge_base_id = ?""",
                (kb_id,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[错误] get_shared_users: {e}")
            return []
        finally:
            conn.close()

    def get_shared_kbs_for_user(self, user_id: int) -> List[Dict]:
        """获取分享给指定用户的知识库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT kb.*, u.username as owner_name,
                   COUNT(DISTINCT d.id) as document_count,
                   COALESCE(SUM(d.chunk_count), 0) as chunk_count,
                   s.shared_by_user_id, bu.username as shared_by_username
                FROM knowledge_base_shares s
                JOIN knowledge_bases kb ON s.knowledge_base_id = kb.id
                JOIN users u ON kb.user_id = u.id
                LEFT JOIN documents d ON kb.id = d.knowledge_base_id
                LEFT JOIN users bu ON s.shared_by_user_id = bu.id
                WHERE s.shared_with_user_id = ?
                GROUP BY kb.id""",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[错误] get_shared_kbs_for_user: {e}")
            return []
        finally:
            conn.close()

    def get_public_kbs(self) -> List[Dict]:
        """获取所有公开知识库"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT kb.*, u.username as owner_name,
               COUNT(DISTINCT d.id) as document_count,
               COALESCE(SUM(d.chunk_count), 0) as chunk_count
            FROM knowledge_bases kb
            JOIN users u ON kb.user_id = u.id
            LEFT JOIN documents d ON kb.id = d.knowledge_base_id
            WHERE kb.visibility = 'public'
            GROUP BY kb.id
            ORDER BY kb.created_at DESC"""
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_kb_visibility(self, kb_id: int, visibility: str, reject_reason: str = ''):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE knowledge_bases SET visibility = ?, reject_reason = ? WHERE id = ?",
                (visibility, reject_reason, kb_id)
            )
            conn.commit()
        except Exception as e:
            print(f"[错误] update_kb_visibility: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_pending_review_kbs(self) -> List[Dict]:
        """获取需要审核的知识库（pending + public + rejected）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT kb.*, u.username as owner_name,
                   COUNT(DISTINCT d.id) as document_count,
                   COALESCE(SUM(d.chunk_count), 0) as chunk_count
                FROM knowledge_bases kb
                JOIN users u ON kb.user_id = u.id
                LEFT JOIN documents d ON kb.id = d.knowledge_base_id
                WHERE kb.visibility IN ('pending', 'public', 'rejected')
                GROUP BY kb.id
                ORDER BY kb.created_at DESC"""
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[错误] get_pending_review_kbs: {e}")
            return []
        finally:
            conn.close()

    # ==================== 点赞/踩操作 ====================

    def vote_knowledge_base(self, kb_id: int, user_id: int, vote_type: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO knowledge_base_votes (knowledge_base_id, user_id, vote_type) VALUES (?, ?, ?)",
                (kb_id, user_id, vote_type)
            )
            conn.commit()
        except Exception as e:
            print(f"[错误] vote_knowledge_base: {e}")
            conn.rollback()
        finally:
            conn.close()

    def remove_vote(self, kb_id: int, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM knowledge_base_votes WHERE knowledge_base_id = ? AND user_id = ?",
                (kb_id, user_id)
            )
            conn.commit()
        except Exception as e:
            print(f"[错误] remove_vote: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_kb_votes(self, kb_id: int) -> Dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT vote_type, COUNT(*) as cnt FROM knowledge_base_votes WHERE knowledge_base_id = ? GROUP BY vote_type",
                (kb_id,)
            )
            votes = {r["vote_type"]: r["cnt"] for r in cursor.fetchall()}
            return {"likes": votes.get("like", 0), "dislikes": votes.get("dislike", 0)}
        except Exception as e:
            print(f"[错误] get_kb_votes: {e}")
            return {"likes": 0, "dislikes": 0}
        finally:
            conn.close()

    def get_user_vote(self, kb_id: int, user_id: int) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT vote_type FROM knowledge_base_votes WHERE knowledge_base_id = ? AND user_id = ?",
                (kb_id, user_id)
            )
            row = cursor.fetchone()
            return row["vote_type"] if row else None
        except Exception as e:
            print(f"[错误] get_user_vote: {e}")
            return None
        finally:
            conn.close()

    # ==================== 举报操作 ====================

    def report_document(self, doc_id: int, user_id: int, reason: str = "") -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO document_reports (document_id, user_id, reason) VALUES (?, ?, ?)",
            (doc_id, user_id, reason)
        )
        conn.commit()
        report_id = cursor.lastrowid
        conn.close()
        return report_id

    def get_reports(self, status: str = None) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if status:
                cursor.execute(
                    """SELECT r.*, u.username, d.filename, d.knowledge_base_id,
                       kb.name as kb_name
                    FROM document_reports r
                    JOIN users u ON r.user_id = u.id
                    LEFT JOIN documents d ON r.document_id = d.id
                    LEFT JOIN knowledge_bases kb ON d.knowledge_base_id = kb.id
                    WHERE r.status = ? ORDER BY r.created_at DESC""",
                    (status,)
                )
            else:
                cursor.execute(
                    """SELECT r.*, u.username, d.filename, d.knowledge_base_id,
                       kb.name as kb_name
                    FROM document_reports r
                    JOIN users u ON r.user_id = u.id
                    LEFT JOIN documents d ON r.document_id = d.id
                    LEFT JOIN knowledge_bases kb ON d.knowledge_base_id = kb.id
                    ORDER BY r.created_at DESC"""
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[错误] get_reports: {e}")
            return []
        finally:
            conn.close()

    def update_report_status(self, report_id: int, status: str, resolve_reason: str = ''):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE document_reports SET status = ?, resolve_reason = ? WHERE id = ?",
                (status, resolve_reason, report_id)
            )
            conn.commit()
        except Exception as e:
            print(f"[错误] update_report_status: {e}")
            conn.rollback()
        finally:
            conn.close()

    # ==================== 收藏操作 ====================

    def favorite_document(self, doc_id: int, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO document_favorites (document_id, user_id) VALUES (?, ?)",
            (doc_id, user_id)
        )
        conn.commit()
        conn.close()

    def unfavorite_document(self, doc_id: int, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM document_favorites WHERE document_id = ? AND user_id = ?",
            (doc_id, user_id)
        )
        conn.commit()
        conn.close()

    def get_user_favorites(self, user_id: int) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT d.*, kb.name as kb_name FROM document_favorites f
            JOIN documents d ON f.document_id = d.id
            JOIN knowledge_bases kb ON d.knowledge_base_id = kb.id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC""",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def is_favorited(self, doc_id: int, user_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM document_favorites WHERE document_id = ? AND user_id = ?",
            (doc_id, user_id)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    # ==================== 用户搜索（分享用） ====================

    def search_users(self, keyword: str) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username FROM users WHERE username LIKE ? LIMIT 10",
            (f"%{keyword}%",)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ==================== 知识库收藏 ====================

    def favorite_knowledge_base(self, kb_id: int, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO knowledge_base_favorites (knowledge_base_id, user_id) VALUES (?, ?)",
            (kb_id, user_id)
        )
        conn.commit()
        conn.close()

    def unfavorite_knowledge_base(self, kb_id: int, user_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM knowledge_base_favorites WHERE knowledge_base_id = ? AND user_id = ?",
            (kb_id, user_id)
        )
        conn.commit()
        conn.close()

    def is_kb_favorited(self, kb_id: int, user_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM knowledge_base_favorites WHERE knowledge_base_id = ? AND user_id = ?",
            (kb_id, user_id)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_user_kb_favorites(self, user_id: int) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT kb.*, u.username as owner_name FROM knowledge_base_favorites f
            JOIN knowledge_bases kb ON f.knowledge_base_id = kb.id
            JOIN users u ON kb.user_id = u.id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC""",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]


# 全局数据库实例
db = Database()
