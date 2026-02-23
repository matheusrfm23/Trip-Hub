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
        
        # Converte JSON Strings para objetos
        for col in ["votes", "extra_data"]:
            if data.get(col):
                try:
                    data[col] = json.loads(data[col])
                except:
                    data[col] = [] if col == "votes" else {}
            else:
                data[col] = [] if col == "votes" else {}

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
            extra_data = json.dumps({}, ensure_ascii=False)
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO places (
                    id, country, category, name, description, lat, lon,
                    maps_link, visited, votes, extra_data, added_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_id, data.get("country"), data.get("category"), data.get("name"),
                data.get("description", ""), data.get("lat", 0.0), data.get("lon", 0.0),
                data.get("maps_link", ""), 0, votes, extra_data,
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
            allowed_cols = ["name", "description", "lat", "lon", "maps_link", "visited", "extra_data"]
            set_clauses = []
            values = []

            for key, value in updated_data.items():
                if key in allowed_cols:
                    set_clauses.append(f"{key} = ?")
                    if key == "extra_data" and isinstance(value, dict):
                        values.append(json.dumps(value, ensure_ascii=False))
                    elif key == "visited":
                         values.append(1 if value else 0)
                    else:
                        values.append(value)
            
            if not set_clauses:
                return False

            values.append(place_id)
            sql = f"UPDATE places SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            
            if cursor.rowcount > 0:
                log.info(f"Local atualizado: {place_id}")
                return True
            return False
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
            # Valida country/category para segurança extra (opcional, mas bom pra consistência)
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
            
            # 1. Busca os votos atuais
            cursor.execute("SELECT votes FROM places WHERE id = ?", (place_id,))
            row = cursor.fetchone()
            
            if not row: return False

            votes_json = row["votes"]
            votes = []
            if votes_json:
                try: votes = json.loads(votes_json)
                except: pass

            # 2. Toggle lógica
            if user_id in votes:
                votes.remove(user_id)
            else:
                votes.append(user_id)

            # 3. Salva de volta
            new_votes_json = json.dumps(votes, ensure_ascii=False)
            cursor.execute("UPDATE places SET votes = ? WHERE id = ?", (new_votes_json, place_id))
            conn.commit()

            return True
        except Exception as e:
            log.error(f"Erro toggle_vote: {e}")
            return False
        finally:
            conn.close()
