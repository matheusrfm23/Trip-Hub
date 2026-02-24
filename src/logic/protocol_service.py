from src.data.database import Database
from src.core.logger import get_logger
from src.core.profiler import track_execution

log = get_logger("ProtocolService")

class ProtocolService:
    @staticmethod
    @track_execution(threshold=0.2)
    async def has_read(user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT has_read FROM protocol_reads WHERE user_id = ?", (str(user_id),))
            row = cursor.fetchone()
            if row:
                return bool(row["has_read"])
            return False
        except Exception as e:
            log.error(f"Erro has_read protocol: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    @track_execution(threshold=0.5)
    async def mark_as_read(user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO protocol_reads (user_id, has_read) VALUES (?, 1)",
                (str(user_id),)
            )
            conn.commit()
            return True
        except Exception as e:
            log.error(f"Erro mark_as_read protocol: {e}")
            return False
        finally:
            conn.close()