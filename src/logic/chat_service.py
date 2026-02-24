# ARQUIVO: src/logic/chat_service.py
import uuid
import time
import asyncio
from src.data.database import Database
from src.core.logger import get_logger
from src.core.profiler import track_execution

log = get_logger("ChatService")

class ChatService:
    @classmethod
    @track_execution(threshold=0.5)
    async def send_message(cls, sender_id, receiver_id, content):
        if not content or not content.strip(): return False
        
        conn = Database.get_connection()
        try:
            msg_id = str(uuid.uuid4())
            timestamp = time.time()
            log.info(f"Enviando msg de {sender_id} para {receiver_id}")
            
            conn.execute('''
                INSERT INTO messages (id, sender_id, receiver_id, content, timestamp, is_read)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (msg_id, sender_id, receiver_id, content, timestamp))
            conn.commit()
            return True
        except Exception as e:
            log.error(f"Erro ao gravar mensagem: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def get_conversation(cls, user1_id, user2_id, limit=50):
        # Pequeno delay para não travar a UI em loops rápidos
        await asyncio.sleep(0.01)
        
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
            log.error(f"Erro ao ler chat: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def mark_conversation_as_read(cls, my_id, other_user_id):
        conn = Database.get_connection()
        try:
            conn.execute('''
                UPDATE messages SET is_read = 1 
                WHERE sender_id = ? AND receiver_id = ?
            ''', (other_user_id, my_id))
            conn.commit()
        except Exception as e:
            log.error(f"Erro mark_conversation_as_read: {e}")
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.2)
    async def get_unread_from(cls, my_id, sender_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM messages 
                WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
            ''', (my_id, sender_id))
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            log.error(f"Erro get_unread_from: {e}")
            return 0
        finally:
            conn.close()