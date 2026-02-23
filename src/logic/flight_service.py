import json
import os
import uuid
import asyncio 
from src.core.locker import file_lock
from src.core.logger import get_logger

# Logger específico
log = get_logger("FlightService")

class FlightService:
    FILE_PATH = os.path.join("assets", "data", "flights.json")
    
    # --- CACHE EM MEMÓRIA (RAM) ---
    _cache_flights = None
    # ------------------------------

    @classmethod
    def _init_db(cls):
        os.makedirs(os.path.dirname(cls.FILE_PATH), exist_ok=True)
        if not os.path.exists(cls.FILE_PATH):
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump([], f)

    @classmethod
    def _ensure_cache(cls):
        """Carrega do disco para a RAM se estiver vazio."""
        if cls._cache_flights is None:
            cls._init_db()
            try:
                with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                    cls._cache_flights = json.load(f)
                log.info(f"Cache de voos carregado: {len(cls._cache_flights)} registros.")
            except Exception as e:
                log.error(f"Erro ao carregar cache de voos: {e}")
                cls._cache_flights = []

    @classmethod
    def _persist_changes(cls):
        """Salva o Cache da RAM no Disco (Write-Through)."""
        try:
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cls._cache_flights, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            log.critical(f"ERRO DE PERSISTÊNCIA (VOOS): {e}")
            return False

    @classmethod
    async def get_flights(cls):
        """Retorna a lista de voos da memória (Instantâneo)."""
        # Substitui time.sleep por asyncio.sleep para não travar o server
        # (Opcional: removemos o sleep artificial para máxima velocidade)
        cls._ensure_cache()
        return cls._cache_flights

    @classmethod
    async def add_flight(cls, flight_data):
        try:
            cls._ensure_cache()
            
            # Geração de ID
            if not flight_data.get("id"):
                flight_data["id"] = str(uuid.uuid4())
                
            # 1. Atualiza RAM
            cls._cache_flights.append(flight_data)
            
            # 2. Persiste Disco
            cls._persist_changes()
            
            log.info(f"Voo adicionado: {flight_data.get('locator', 'N/A')}")
            return True
        except Exception as e:
            log.error(f"Erro ao adicionar voo: {e}")
            return False

    @classmethod
    async def update_flight(cls, flight_id, new_data):
        try:
            cls._ensure_cache()
            updated = False
            
            for i, f in enumerate(cls._cache_flights):
                if f["id"] == flight_id:
                    new_data["id"] = flight_id # Garante integridade do ID
                    cls._cache_flights[i] = new_data # Atualiza na RAM
                    updated = True
                    break
            
            if updated:
                cls._persist_changes() # Salva no disco
                log.info(f"Voo atualizado: {flight_id}")
                return True
            return False
        except Exception as e: 
            log.error(f"Erro ao atualizar voo: {e}")
            return False

    @classmethod
    async def delete_flight(cls, flight_id):
        try:
            cls._ensure_cache()
            initial_len = len(cls._cache_flights)
            
            # Filtra na RAM
            cls._cache_flights = [f for f in cls._cache_flights if f["id"] != flight_id]
            
            if len(cls._cache_flights) != initial_len:
                cls._persist_changes()
                log.info(f"Voo removido: {flight_id}")
                return True
            return False
        except Exception as e: 
            log.error(f"Erro ao deletar voo: {e}")
            return False

    @classmethod
    def clean_orphaned_flights(cls, valid_user_ids):
        """
        Garbage Collector. (Síncrono pois roda no boot).
        """
        try:
            cls._ensure_cache()
            initial_count = len(cls._cache_flights)
            
            # Filtra apenas voos de usuários válidos
            cls._cache_flights = [f for f in cls._cache_flights if str(f.get("user_id")) in valid_user_ids]
            
            if len(cls._cache_flights) != initial_count:
                cls._persist_changes()
                log.info(f"[Limpeza] Voos órfãos removidos: {initial_count - len(cls._cache_flights)}")
        except Exception as e:
            log.error(f"Erro na limpeza de voos: {e}")

    @classmethod
    async def get_user_flights(cls, user_id):
        cls._ensure_cache()
        # Filtro em memória (Rápido)
        return [f for f in cls._cache_flights if str(f.get("user_id")) == str(user_id)]
        
    @classmethod
    async def delete_all_from_user(cls, user_id):
        cls._ensure_cache()
        cls._cache_flights = [f for f in cls._cache_flights if str(f.get("user_id")) != str(user_id)]
        cls._persist_changes()