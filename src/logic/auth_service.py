import json
import uuid
import time
import os
import asyncio
from src.data.database import Database
from src.logic.flight_service import FlightService
from src.logic.finance_service import FinanceService
from src.core.logger import get_logger
from src.core.profiler import track_execution

log = get_logger("AuthService")

class AuthService:
    # Lê do ambiente ou usa fallback seguro
    MASTER_PIN = os.getenv("MASTER_PIN", "0000")

    TEMPLATE_CONTACT = {
        "phone": "", "email": "", 
        "emergency_name": "", "emergency_phone": ""
    }
    
    TEMPLATE_MEDICAL = {
        "blood_type": "Não sei", 
        "donor": False, 
        "allergies": "", 
        "medications": "", 
        "vaccines": "",
        "notes": "",
        "doctor": {"name": "", "phone": ""},
        "health_plan": {"active": False, "name": "", "number": "", "phone": ""},
        "funeral_plan": {"active": False, "name": "", "phone": ""}
    }

    @classmethod
    def _row_to_dict(cls, row):
        """Converte sqlite3.Row para dicionário e processa colunas JSON."""
        if not row:
            return None

        user = dict(row)

        # Colunas que armazenam JSON strings
        json_cols = ["privacy", "contact", "medical", "last_location"]

        for col in json_cols:
            val = user.get(col)
            if val and str(val).strip():
                try:
                    user[col] = json.loads(val)
                except Exception as e:
                    # Fallback para dados legados ou strings puras em last_location
                    if col == "last_location":
                        user[col] = val
                    else:
                        log.error(f"Erro ao decodificar JSON da coluna {col}: {e}")
                        user[col] = {}
            else:
                 # Valores padrão para campos vazios
                 if col == "last_location":
                     user[col] = ""
                 else:
                     user[col] = {}

        return user

    @classmethod
    @track_execution(threshold=2.0)
    async def perform_integrity_check(cls):
        """Orquestrador de limpeza de dados via SQLite"""
        log.info("Iniciando Verificação de Integridade dos Dados...")
        
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users")
            rows = cursor.fetchall()
            valid_ids = [row["id"] for row in rows]

            # Limpezas externas
            FlightService.clean_orphaned_flights(valid_ids)
            await FinanceService.clean_orphaned_finances(valid_ids)

            log.info(f"Verificação Concluída. {len(valid_ids)} perfis ativos.")
        except Exception as e:
            log.error(f"Erro na verificação de integridade: {e}")
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def get_profiles(cls):
        """Retorna todos os perfis do SQLite."""
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            return [cls._row_to_dict(row) for row in rows]
        except Exception as e:
            log.error(f"Erro ao buscar perfis: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def get_user_by_id(cls, user_id):
        """Busca usuário por ID."""
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
            row = cursor.fetchone()
            return cls._row_to_dict(row)
        except Exception as e:
            log.error(f"Erro ao buscar usuário {user_id}: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def login(cls, user_id, pin):
        """Login direto no banco."""
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ? AND pin = ?", (str(user_id), str(pin)))
            row = cursor.fetchone()
            
            user = cls._row_to_dict(row)
            if user:
                log.info(f"Login realizado com sucesso: {user['name']}")
                return user

            log.warning(f"Falha de login para ID: {user_id}")
            return None
        except Exception as e:
            log.error(f"Erro no login: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=1.0)
    async def create_profile(cls, name, pin):
        conn = Database.get_connection()
        try:
            log.info(f"Tentando criar perfil: {name}")
            cursor = conn.cursor()
            
            # Verifica se já existem usuários para definir ROLE
            cursor.execute("SELECT COUNT(*) as count FROM users")
            row = cursor.fetchone()
            count = row["count"] if row else 0
            role = "ADMIN" if count == 0 else "USER"
            
            new_id = str(uuid.uuid4())
            
            # Dados iniciais serializados
            privacy = json.dumps({"passport": False, "medical": True}, ensure_ascii=False)
            contact = json.dumps(cls.TEMPLATE_CONTACT, ensure_ascii=False)
            medical = json.dumps(cls.TEMPLATE_MEDICAL, ensure_ascii=False)
            last_location = json.dumps("", ensure_ascii=False)
            
            cursor.execute('''
                INSERT INTO users (
                    id, name, role, pin, avatar, passport, cpf, rg,
                    privacy, contact, medical, last_seen, last_location, status_msg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_id, name, role, pin, None, "", "", "",
                privacy, contact, medical, 0, last_location, "Disponível"
            ))

            conn.commit()
            log.info(f"Perfil criado: {name} ({new_id})")
            return True
        except Exception as e:
            log.error(f"Erro crítico ao criar perfil: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.5)
    async def update_profile_general(cls, profile_id, updates):
        conn = Database.get_connection()
        try:
            # Lista de colunas permitidas para evitar SQL Injection via chaves do dict
            allowed_cols = [
                "name", "role", "pin", "avatar", "passport", "cpf", "rg",
                "privacy", "contact", "medical", "last_seen", "last_location", "status_msg"
            ]
            
            set_clauses = []
            values = []

            for key, value in updates.items():
                if key in allowed_cols:
                    set_clauses.append(f"{key} = ?")
                    # Se for dict/list, dump para JSON
                    if isinstance(value, (dict, list)):
                        values.append(json.dumps(value, ensure_ascii=False))
                    else:
                        values.append(value)

            if not set_clauses:
                return False
                
            values.append(str(profile_id))
            sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"

            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()

            if cursor.rowcount > 0:
                log.info(f"Perfil atualizado: {profile_id}")
                return True
            return False
        except Exception as e: 
            log.error(f"Erro ao atualizar perfil: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=0.2)
    async def update_presence(cls, user_id, location=None, status_msg=None, is_heartbeat=False):
        conn = Database.get_connection()
        try:
            set_clauses = ["last_seen = ?"]
            values = [time.time()]
            
            if location is not None:
                set_clauses.append("last_location = ?")
                if isinstance(location, (dict, list)):
                     values.append(json.dumps(location, ensure_ascii=False))
                else:
                     values.append(str(location))
                
            if status_msg is not None:
                set_clauses.append("status_msg = ?")
                values.append(status_msg)
            
            values.append(str(user_id))
            
            sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            
            return True
        except Exception as e:
            if not is_heartbeat:
                log.error(f"Erro ao atualizar presença: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    @track_execution(threshold=1.0)
    async def delete_profile(cls, profile_id):
        log.warning(f"Solicitação de exclusão de perfil: {profile_id}")
        conn = Database.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (str(profile_id),))
            conn.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                log.info(f"Perfil excluído com sucesso: {profile_id}")
            else:
                 log.warning(f"Perfil não encontrado para exclusão: {profile_id}")

            return deleted
        except Exception as e:
            log.critical(f"Erro Crítico ao Deletar: {e}")
            return False
        finally:
            conn.close()
            # Se deletou, roda integridade (cria nova conexão dentro do método)
            if 'deleted' in locals() and deleted:
                await cls.perform_integrity_check()
