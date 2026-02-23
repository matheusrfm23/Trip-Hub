# ARQUIVO: src/logic/chat_service.py
import uuid
import time
import asyncio
from src.data.database import Database

class ChatService:
    
    @classmethod
    def _ensure_table(cls):
        """Garante que a tabela de mensagens existe (Auto-correção)"""
        try:
            conn = Database.get_connection()
            try:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        sender_id TEXT NOT NULL,
                        receiver_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        is_read INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()
            finally:
                conn.close() # <--- BLINDAGEM
        except Exception as e:
            print(f"Erro ao verificar tabela messages: {e}")

    @classmethod
    async def send_message(cls, sender_id, receiver_id, content):
        if not content or not content.strip(): return False
        cls._ensure_table()
        
        conn = Database.get_connection()
        try:
            msg_id = str(uuid.uuid4())
            timestamp = time.time()
            print(f"Enviando msg de {sender_id} para {receiver_id}")
            
            conn.execute('''
                INSERT INTO messages (id, sender_id, receiver_id, content, timestamp, is_read)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (msg_id, sender_id, receiver_id, content, timestamp))
            conn.commit()
            return True
        except Exception as e:
            print(f"CRITICAL: Erro ao gravar mensagem: {e}")
            return False
        finally:
            conn.close() # <--- BLINDAGEM

    @classmethod
    async def get_conversation(cls, user1_id, user2_id, limit=50):
        cls._ensure_table()
        await asyncio.sleep(0.01) # Não trava a UI
        
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            query = '''
                SELECT * FROM messages 
                WHERE (sender_id = ? AND receiver_id = ?) 
                   OR (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp DESC
                LIMIT ?
            '''
            cursor.execute(query, (user1_id, user2_id, user2_id, user1_id, limit))
            rows = cursor.fetchall()
            messages = [dict(row) for row in rows]
            return messages[::-1] 
        except Exception as e:
            print(f"Erro ao ler chat: {e}")
            return []
        finally:
            conn.close() # <--- BLINDAGEM

    @classmethod
    async def mark_conversation_as_read(cls, my_id, other_user_id):
        conn = Database.get_connection()
        try:
            conn.execute('''
                UPDATE messages SET is_read = 1 
                WHERE sender_id = ? AND receiver_id = ?
            ''', (other_user_id, my_id))
            conn.commit()
        except: pass
        finally:
            conn.close() # <--- BLINDAGEM

    @classmethod
    async def get_unread_from(cls, my_id, sender_id):
        cls._ensure_table()
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM messages 
                WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
            ''', (my_id, sender_id))
            count = cursor.fetchone()[0]
            return count
        except: return 0
        finally:
            conn.close() # <--- BLINDAGEM