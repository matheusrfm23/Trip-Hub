# ARQUIVO: src/logic/notification_service.py
import json
import uuid
import asyncio
from datetime import datetime
from src.data.database import Database
from src.core.logger import get_logger
from src.core.profiler import track_execution

log = get_logger("NotificationService")

class NotificationService:
    @staticmethod
    def _row_to_dict(row):
        if not row: return None
        data = dict(row)
        if data.get("read_by"):
            try:
                data["read_by"] = json.loads(data["read_by"])
            except:
                data["read_by"] = []
        else:
            data["read_by"] = []
        return data

    @classmethod
    @track_execution(threshold=0.5)
    async def get_notifications(cls, user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM notifications WHERE target_id = 'ALL' OR target_id = ? ORDER BY timestamp DESC",
                (str(user_id),)
            )
            rows = cursor.fetchall()
            return [cls._row_to_dict(row) for row in rows]
        except Exception as e:
            log.error(f"Erro ao buscar notificações: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.2)
    async def get_unread_count(cls, user_id):
        conn = Database.get_connection()
        try:
            # Busca todas e filtra no Python por simplicidade (devido ao JSON)
            # Otimização futura: usar JSON_EACH do SQLite se disponível
            notifs = await cls.get_notifications(user_id)
            count = 0
            for n in notifs:
                if str(user_id) not in n.get("read_by", []):
                    count += 1
            return count
        except Exception as e:
            log.error(f"Erro count notificações: {e}")
            return 0
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def mark_as_read(cls, notif_id, user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT read_by FROM notifications WHERE id = ?", (notif_id,))
            row = cursor.fetchone()
            if not row: return False
            
            read_by = []
            if row["read_by"]:
                try: read_by = json.loads(row["read_by"])
                except: pass

            if str(user_id) not in read_by:
                read_by.append(str(user_id))
                new_json = json.dumps(read_by, ensure_ascii=False)
                cursor.execute("UPDATE notifications SET read_by = ? WHERE id = ?", (new_json, notif_id))
                conn.commit()
                return True
            return False
        except Exception as e:
            log.error(f"Erro mark_as_read: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=1.0)
    async def mark_all_read(cls, user_id):
        # Implementação iterativa segura
        notifs = await cls.get_notifications(user_id)
        for n in notifs:
            await cls.mark_as_read(n["id"], user_id)
        return True

    @classmethod
    @track_execution(threshold=0.5)
    async def send_notification(cls, sender_name, target_id, title, message, type="info"):
        conn = Database.get_connection()
        try:
            new_id = str(uuid.uuid4())
            ts = datetime.now().strftime("%d/%m %H:%M") # Formato legado
            read_by = json.dumps([], ensure_ascii=False)
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (id, sender, target_id, title, message, type, timestamp, read_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (new_id, sender_name, str(target_id), title, message, type, ts, read_by))
            conn.commit()
            return True
        except Exception as e:
            log.error(f"Erro send_notification: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=1.0)
    async def clear_all(cls):
        """Apaga TODAS as notificações (Admin)."""
        conn = Database.get_connection()
        try:
            conn.execute("DELETE FROM notifications")
            conn.commit()
            log.warning("Todas as notificações foram apagadas.")
            return True
        except Exception as e:
            log.error(f"Erro clear_all: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def delete_notification(cls, notif_id):
        conn = Database.get_connection()
        try:
            conn.execute("DELETE FROM notifications WHERE id = ?", (notif_id,))
            conn.commit()
            return True
        except Exception as e:
            log.error(f"Erro delete_notification: {e}")
            return False
        finally:
            conn.close()
