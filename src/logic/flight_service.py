import json
import uuid
import asyncio 
from src.data.database import Database
from src.core.logger import get_logger
from src.core.profiler import track_execution

# Logger específico
log = get_logger("FlightService")

class FlightService:
    @staticmethod
    def _row_to_dict(row):
        if not row: return None
        data = dict(row)

        # Details é JSON
        if data.get("details"):
            try:
                data.update(json.loads(data["details"]))
            except: pass

        # Remove a coluna raw 'details' para ficar flat como o original
        if "details" in data:
            del data["details"]

        return data

    @classmethod
    @track_execution(threshold=0.5)
    async def get_flights(cls):
        """Retorna a lista de voos do banco."""
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM flights")
            rows = cursor.fetchall()
            return [cls._row_to_dict(row) for row in rows]
        except Exception as e:
            log.error(f"Erro ao buscar voos: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=1.0)
    async def add_flight(cls, flight_data):
        conn = Database.get_connection()
        try:
            # Geração de ID
            new_id = flight_data.get("id") or str(uuid.uuid4())
            
            # Separa colunas fixas de detalhes variáveis
            fixed_cols = ["id", "user_id", "locator", "passenger"]
            details = {k: v for k, v in flight_data.items() if k not in fixed_cols}
            details_json = json.dumps(details, ensure_ascii=False)
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flights (id, user_id, locator, passenger, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                new_id,
                flight_data.get("user_id"),
                flight_data.get("locator"),
                flight_data.get("passenger"),
                details_json
            ))

            conn.commit()
            log.info(f"Voo adicionado: {flight_data.get('locator', 'N/A')}")
            return True
        except Exception as e:
            log.error(f"Erro ao adicionar voo: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def update_flight(cls, flight_id, new_data):
        conn = Database.get_connection()
        try:
            # Primeiro busca o atual para fazer merge dos details
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
            row = cursor.fetchone()
            if not row: return False
            
            current_details = {}
            if row["details"]:
                try: current_details = json.loads(row["details"])
                except: pass

            # Atualiza colunas fixas se vierem
            fixed_cols = ["user_id", "locator", "passenger"]
            sql_parts = []
            values = []
            
            for col in fixed_cols:
                if col in new_data:
                    sql_parts.append(f"{col} = ?")
                    values.append(new_data[col])

            # Atualiza details (Merge)
            extra_data = {k: v for k, v in new_data.items() if k not in fixed_cols and k != "id"}
            current_details.update(extra_data)

            sql_parts.append("details = ?")
            values.append(json.dumps(current_details, ensure_ascii=False))

            values.append(flight_id)

            sql = f"UPDATE flights SET {', '.join(sql_parts)} WHERE id = ?"
            cursor.execute(sql, values)
            conn.commit()

            log.info(f"Voo atualizado: {flight_id}")
            return True
        except Exception as e: 
            log.error(f"Erro ao atualizar voo: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=1.0)
    async def delete_flight(cls, flight_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM flights WHERE id = ?", (flight_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                log.info(f"Voo removido: {flight_id}")
                return True
            return False
        except Exception as e: 
            log.error(f"Erro ao deletar voo: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def clean_orphaned_flights(cls, valid_user_ids):
        """
        Garbage Collector. (Síncrono pois roda no boot).
        """
        conn = Database.get_connection()
        try:
            # Placeholder String para a query IN (?, ?, ...)
            placeholders = ', '.join(['?'] * len(valid_user_ids))
            sql = f"DELETE FROM flights WHERE user_id NOT IN ({placeholders})"
            
            cursor = conn.cursor()
            cursor.execute(sql, valid_user_ids)
            conn.commit()
            
            if cursor.rowcount > 0:
                log.info(f"[Limpeza] Voos órfãos removidos: {cursor.rowcount}")
        except Exception as e:
            log.error(f"Erro na limpeza de voos: {e}")
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def get_user_flights(cls, user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM flights WHERE user_id = ?", (str(user_id),))
            rows = cursor.fetchall()
            return [cls._row_to_dict(row) for row in rows]
        except Exception as e:
            log.error(f"Erro ao buscar voos do usuario {user_id}: {e}")
            return []
        finally:
            conn.close()
        
    @classmethod
    @track_execution(threshold=1.0)
    async def delete_all_from_user(cls, user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM flights WHERE user_id = ?", (str(user_id),))
            conn.commit()
            log.info(f"Voos apagados para usuário: {user_id}")
        except Exception as e:
            log.error(f"Erro delete_all_from_user: {e}")
        finally:
            conn.close()
