# ARQUIVO: src/logic/place_service.py
import json
import uuid
import asyncio
from src.data.database import Database
from src.core.logger import get_logger
from src.core.profiler import track_execution

log = get_logger("PlaceService")

class PlaceService:
    @staticmethod
    def _row_to_dict(row):
        if not row: return None
        data = dict(row)
        
        # 1. Processa JSON fields
        votes = []
        if data.get("votes"):
            try: votes = json.loads(data["votes"])
            except: pass
        data["votes"] = votes

        extra_data = {}
        if data.get("extra_data"):
            try: extra_data = json.loads(data["extra_data"])
            except: pass

        # 2. Flatten extra_data into main dict (CORREÇÃO PEDIDA)
        data.update(extra_data)

        # 3. Remove raw JSON columns to clean up
        if "extra_data" in data: del data["extra_data"]

        # Boolean conversion
        data["visited"] = bool(data.get("visited", 0))
        return data

    @staticmethod
    @track_execution(threshold=0.5)
    async def get_places(country_code, category):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM places WHERE country = ? AND category = ? ORDER BY id DESC",
                (country_code, category)
            )
            rows = cursor.fetchall()
            return [PlaceService._row_to_dict(row) for row in rows]
        except Exception as e:
            log.error(f"Erro ao buscar locais ({country_code}/{category}): {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    @track_execution(threshold=1.0)
    async def add_place(data):
        conn = Database.get_connection()
        try:
            new_id = str(uuid.uuid4())
            votes = json.dumps([], ensure_ascii=False)

            # Separa campos fixos de extra_data
            fixed_cols = ["country", "category", "name", "description", "lat", "lon", "maps_link", "added_by"]
            extra = {k: v for k, v in data.items() if k not in fixed_cols and k != "id"}
            extra_data_json = json.dumps(extra, ensure_ascii=False)
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO places (
                    id, country, category, name, description, lat, lon,
                    maps_link, visited, votes, extra_data, added_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_id, data.get("country"), data.get("category"), data.get("name"),
                data.get("description", ""), data.get("lat", 0.0), data.get("lon", 0.0),
                data.get("maps_link", ""), 0, votes, extra_data_json,
                data.get("added_by", "system")
            ))
            
            conn.commit()
            log.info(f"Local adicionado: {data.get('name')} ({new_id})")
            return True
        except Exception as e:
            log.error(f"Erro ao adicionar local: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    @track_execution(threshold=0.5)
    async def update_place(place_id, updated_data):
        conn = Database.get_connection()
        try:
            # Busca dados atuais para merge do extra_data
            cursor = conn.cursor()
            cursor.execute("SELECT extra_data FROM places WHERE id = ?", (place_id,))
            row = cursor.fetchone()
            if not row: return False

            current_extra = {}
            if row["extra_data"]:
                try: current_extra = json.loads(row["extra_data"])
                except: pass

            # Campos fixos
            allowed_cols = ["name", "description", "lat", "lon", "maps_link", "visited"]
            set_clauses = []
            values = []

            for key, value in updated_data.items():
                if key in allowed_cols:
                    set_clauses.append(f"{key} = ?")
                    if key == "visited": values.append(1 if value else 0)
                    else: values.append(value)

            # Merge extra_data
            new_extra = {k: v for k, v in updated_data.items() if k not in allowed_cols and k != "id"}
            if new_extra:
                current_extra.update(new_extra)
                set_clauses.append("extra_data = ?")
                values.append(json.dumps(current_extra, ensure_ascii=False))

            if not set_clauses: return False

            values.append(place_id)
            sql = f"UPDATE places SET {', '.join(set_clauses)} WHERE id = ?"

            cursor.execute(sql, values)
            conn.commit()

            log.info(f"Local atualizado: {place_id}")
            return True
        except Exception as e:
            log.error(f"Erro update_place: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    @track_execution(threshold=1.0)
    async def delete_place(place_id, country_code, category):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM places WHERE id = ? AND country = ? AND category = ?",
                (place_id, country_code, category)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                log.info(f"Local removido: {place_id}")
                return True
            return False
        except Exception as e:
            log.error(f"Erro delete_place: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    @track_execution(threshold=0.5)
    async def toggle_vote(place_id, country_code, category, user_id):
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT votes FROM places WHERE id = ?", (place_id,))
            row = cursor.fetchone()
            
            if not row: return False

            votes = []
            if row["votes"]:
                try: votes = json.loads(row["votes"])
                except: pass

            if user_id in votes: votes.remove(user_id)
            else: votes.append(user_id)

            new_votes_json = json.dumps(votes, ensure_ascii=False)
            cursor.execute("UPDATE places SET votes = ? WHERE id = ?", (new_votes_json, place_id))
            conn.commit()
            return True
        except Exception as e:
            log.error(f"Erro toggle_vote: {e}")
            return False
        finally:
            conn.close()
