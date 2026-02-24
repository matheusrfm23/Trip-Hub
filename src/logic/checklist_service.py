import json
from src.data.database import Database
from src.core.logger import get_logger
from src.core.profiler import track_execution

log = get_logger("ChecklistService")

class ChecklistService:
    @staticmethod
    @track_execution(threshold=0.5)
    async def get_checklist(user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT items FROM checklists WHERE user_id = ?", (str(user_id),))
            row = cursor.fetchone()

            if row and row["items"]:
                try:
                    return json.loads(row["items"])
                except Exception as e:
                    log.error(f"Erro ao decodificar checklist do usuario {user_id}: {e}")
                    return []
            return []
        except Exception as e:
            log.error(f"Erro get_checklist: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    @track_execution(threshold=0.5)
    async def save_checklist(user_id, items):
        conn = Database.get_connection()
        try:
            items_json = json.dumps(items, ensure_ascii=False)
            cursor = conn.cursor()
            # INSERT OR REPLACE funciona como um Upsert simplificado no SQLite
            cursor.execute(
                "INSERT OR REPLACE INTO checklists (user_id, items) VALUES (?, ?)",
                (str(user_id), items_json)
            )
            conn.commit()
            return True
        except Exception as e:
            log.error(f"Erro ao salvar checklist: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    @track_execution(threshold=0.5)
    async def reset_checks(user_id):
        """Zera os 'checks' mas mantém os itens"""
        try:
            # Pega do banco
            items = await ChecklistService.get_checklist(user_id)

            if not items: return True
            
            # Modifica em memória
            for item in items:
                item["checked"] = False

            # Salva de volta
            return await ChecklistService.save_checklist(user_id, items)
        except Exception as e:
            log.error(f"Erro reset_checks: {e}")
            return False