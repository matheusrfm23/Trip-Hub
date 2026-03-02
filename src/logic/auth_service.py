# ARQUIVO: src/logic/auth_service.py
import json
import os
import uuid
import time
import asyncio
from src.logic.flight_service import FlightService
from src.logic.finance_service import FinanceService
from src.core.locker import file_lock
from src.core.logger import get_logger
from src.core.profiler import monitor

# Inicializa o logger específico para este serviço
log = get_logger("AuthService")

class AuthService:
    FILE_PATH = os.path.join("assets", "data", "profiles.json")
    CACHE_PATH = os.path.join("assets", "data", "cache.json") 
    # [CORREÇÃO] Lê do ambiente ou usa fallback seguro
    MASTER_PIN = os.getenv("MASTER_PIN", "0000")

    # --- CAMADA DE CACHE (RAM) ---
    # Armazena um mapa {id: profile} para acesso O(1) imediato
    # Esta é a ÚNICA fonte de verdade na RAM
    _cache_map = None
    # -----------------------------

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
    def _init_db(cls):
        """Garante que o arquivo físico existe."""
        os.makedirs(os.path.dirname(cls.FILE_PATH), exist_ok=True)
        if not os.path.exists(cls.FILE_PATH):
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=4, ensure_ascii=False)

    @classmethod
    def _refresh_cache(cls):
        """
        Lê do disco e reconstrói o cache de memória.
        Deve ser chamado na inicialização ou quando houver dúvida de integridade.
        """
        cls._init_db()
        try:
            with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Constrói o mapa de acesso rápido como Single Source of Truth
                cls._cache_map = {str(p["id"]): p for p in data}
        except Exception as e:
            log.error(f"Erro ao carregar cache do disco: {e}")
            cls._cache_map = {}

    @classmethod
    def _ensure_cache(cls):
        """Lazy loader para o cache."""
        if cls._cache_map is None:
            cls._refresh_cache()

    @classmethod
    @monitor(threshold=2.0) 
    async def perform_integrity_check(cls):
        """Orquestrador de limpeza de dados"""
        log.info("Iniciando Verificação de Integridade dos Dados...")
        
        # Força atualização do disco para garantir estado fresco no boot
        cls._refresh_cache() 
        
        valid_ids = list(cls._cache_map.keys())
        
        # Limpezas externas
        FlightService.clean_orphaned_flights(valid_ids)
        await FinanceService.clean_orphaned_finances(valid_ids)
        
        log.info(f"Verificação Concluída. {len(valid_ids)} perfis ativos.")

    @classmethod
    async def get_profiles(cls):
        """Retorna todos os perfis (Leitura de RAM, gerada dinamicamente)."""
        cls._ensure_cache()
        return list(cls._cache_map.values())

    @classmethod
    async def get_user_by_id(cls, user_id):
        """
        Busca usuário por ID com performance O(1).
        Ideal para uso intensivo no Router.
        """
        cls._ensure_cache()
        # Busca direta no Hash Map (Instantâneo)
        return cls._cache_map.get(str(user_id))

    @classmethod
    @monitor(threshold=0.5)
    async def login(cls, user_id, pin):
        """Login otimizado via RAM."""
        user = await cls.get_user_by_id(user_id)
        
        if user and str(user.get("pin")) == str(pin):
            log.info(f"Login realizado com sucesso: {user['name']}")
            return user
            
        log.warning(f"Falha de login para ID: {user_id}")
        return None

    @classmethod
    @monitor(threshold=1.0)
    async def create_profile(cls, name, pin):
        try:
            log.info(f"Tentando criar perfil: {name}")
            cls._ensure_cache()
            
            role = "ADMIN" if len(cls._cache_map) == 0 else "USER"

            new_user = {
                "id": str(uuid.uuid4()),
                "name": name,
                "role": role,
                "pin": pin,
                "avatar": None,
                "passport": "",
                "cpf": "",
                "rg": "",
                "privacy": {"passport": False, "medical": True},
                "contact": cls.TEMPLATE_CONTACT.copy(),
                "medical": cls.TEMPLATE_MEDICAL.copy(),
                "last_seen": 0,
                "last_location": "",
                "status_msg": "Disponível"
            }
            
            # 1. Atualiza RAM (Write-Through)
            cls._cache_map[new_user["id"]] = new_user
            
            # 2. Persiste no Disco
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(list(cls._cache_map.values()), f, indent=4, ensure_ascii=False)
            
            log.info(f"Perfil criado: {name} ({new_user['id']})")
            return True
        except Exception as e:
            log.error(f"Erro crítico ao criar perfil: {e}")
            return False

    @classmethod
    @monitor(threshold=0.5)
    async def update_profile_general(cls, profile_id, updates):
        try:
            cls._ensure_cache()
            user = cls._cache_map.get(str(profile_id))
            
            if user:
                # 1. Atualiza objeto na RAM (Reference Update)
                user.update(updates)
                
                # 2. Persiste lista completa no disco
                with file_lock():
                    with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(list(cls._cache_map.values()), f, indent=4, ensure_ascii=False)
                        
                log.info(f"Perfil atualizado: {profile_id}")
                return True
            return False
        except Exception as e: 
            log.error(f"Erro ao atualizar perfil: {e}")
            return False

    @classmethod
    @monitor(threshold=0.2)
    async def update_presence(cls, user_id, location=None, status_msg=None, is_heartbeat=False):
        """
        Atualiza dados voláteis. 
        Otimizado: Atualiza RAM instantaneamente, depois disco.
        """
        try:
            cls._ensure_cache()
            user = cls._cache_map.get(str(user_id))
            
            if user:
                # Atualização Atômica na RAM (Instantânea para a UI)
                user["last_seen"] = time.time()
                if location is not None:
                    user["last_location"] = location
                if status_msg is not None:
                    user["status_msg"] = status_msg
                
                # Persistência (Pode ser removida se quiser que presença seja 100% volátil)
                # Mantivemos para garantir estado entre reboots, mas com lock seguro.
                with file_lock():
                    with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(list(cls._cache_map.values()), f, indent=4, ensure_ascii=False)
                
                return True
            return False
        except Exception as e:
            return False

    @classmethod
    @monitor(threshold=1.0)
    async def delete_profile(cls, profile_id):
        try:
            log.warning(f"Solicitação de exclusão de perfil: {profile_id}")
            cls._ensure_cache()
            
            # Remove from RAM (O(1))
            deleted_user = cls._cache_map.pop(str(profile_id), None)

            if not deleted_user:
                log.warning(f"Perfil {profile_id} não encontrado para exclusão.")
                return False

            # Verifica se o perfil excluído é o logado no momento
            logged_in_id = cls.get_cached_login()
            if logged_in_id and str(logged_in_id) == str(profile_id):
                cls.clear_cached_login()
            
            # Persiste Disco
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(list(cls._cache_map.values()), f, indent=4, ensure_ascii=False)
            
            # Limpeza de dados órfãos
            await cls.perform_integrity_check()
            
            log.info(f"Perfil excluído com sucesso: {profile_id}")
            return True
        except Exception as e:
            log.critical(f"Erro Crítico ao Deletar: {e}")
            return False

    # --- MÉTODOS DE CACHE DE SESSÃO LOCAL (Client Side Helpers) ---
    @classmethod
    def save_cached_login(cls, user_id):
        try:
            os.makedirs(os.path.dirname(cls.CACHE_PATH), exist_ok=True)
            with file_lock():
                with open(cls.CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump({"last_user_id": user_id}, f)
        except Exception as e:
            log.error(f"Erro ao salvar cache: {e}")

    @classmethod
    def get_cached_login(cls):
        if not os.path.exists(cls.CACHE_PATH):
            return None
        try:
            with open(cls.CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_user_id")
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            log.warning(f"Erro ao decodificar cache de login: {e}")
            return None
        except Exception as e:
            log.exception(f"Erro inesperado ao obter cache de login: {e}")
            return None

    @classmethod
    def clear_cached_login(cls):
        if os.path.exists(cls.CACHE_PATH):
            try:
                with file_lock():
                    os.remove(cls.CACHE_PATH)
            except FileNotFoundError:
                pass
            except Exception as e:
                log.error(f"Erro ao remover cache de login: {e}")