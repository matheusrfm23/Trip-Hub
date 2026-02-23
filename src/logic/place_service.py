# ARQUIVO: src/logic/place_service.py
import json
import os
import uuid
import asyncio
from src.core.locker import file_lock
from src.core.logger import get_logger

# Logger específico
log = get_logger("PlaceService")

class PlaceService:
    DATA_DIR = "assets/data"
    
    # --- CACHE DINÂMICO (Map de Listas) ---
    # Chaves serão do tipo "br_hotel", "us_food", etc.
    _cache = {}
    # --------------------------------------

    @classmethod
    def _get_cache_key(cls, country, category):
        return f"{country}_{category}"

    @classmethod
    def _get_file_path(cls, country, category):
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)
        # Usa o mesmo padrão de nome da chave de cache para simplicidade
        filename = f"{cls._get_cache_key(country, category)}.json"
        return os.path.join(cls.DATA_DIR, filename)

    @classmethod
    def _ensure_loaded(cls, country, category):
        """
        Carrega o arquivo específico para a RAM apenas se ainda não estiver lá (Lazy Load).
        """
        key = cls._get_cache_key(country, category)
        
        if key not in cls._cache:
            path = cls._get_file_path(country, category)
            if not os.path.exists(path):
                # Se arquivo não existe, inicia lista vazia na RAM
                cls._cache[key] = []
            else:
                try:
                    # Leitura segura
                    with file_lock():
                        with open(path, "r", encoding="utf-8") as f:
                            cls._cache[key] = json.load(f)
                    log.info(f"Cache carregado: {key} ({len(cls._cache[key])} itens)")
                except Exception as e:
                    log.error(f"Erro ao carregar cache {key}: {e}")
                    cls._cache[key] = []
        
        return cls._cache[key]

    @classmethod
    def _persist(cls, country, category):
        """Salva o cache da RAM no disco (Write-Through)."""
        key = cls._get_cache_key(country, category)
        if key not in cls._cache: return False
        
        path = cls._get_file_path(country, category)
        try:
            with file_lock():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cls._cache[key], f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            log.error(f"Erro ao salvar {key}: {e}")
            return False

    # --- MÉTODOS CRUD (BLINDADOS & INSTANTÂNEOS) ---

    @staticmethod
    async def get_places(country_code, category):
        # Removemos o sleep artificial
        # Carrega (se necessário) e retorna da RAM
        places = PlaceService._ensure_loaded(country_code, category)
        return places[::-1] # Retorna invertido (mais recentes primeiro)

    @staticmethod
    async def add_place(data):
        try:
            country = data["country"]
            category = data["category"]
            
            # 1. Garante que a lista está na memória
            places = PlaceService._ensure_loaded(country, category)
            
            # 2. Atualiza RAM
            data["id"] = str(uuid.uuid4())
            data["visited"] = False
            data["votes"] = [] 
            places.append(data)
            
            # 3. Persiste no Disco
            saved = PlaceService._persist(country, category)
            
            if saved:
                log.info(f"Local adicionado: {data.get('name')} ({country}/{category})")
            return saved
        except Exception as e:
            log.error(f"Erro ao adicionar local: {e}")
            return False

    @staticmethod
    async def update_place(place_id, updated_data):
        try:
            country = updated_data["country"]
            category = updated_data["category"]
            
            places = PlaceService._ensure_loaded(country, category)
            found = False
            
            for i, place in enumerate(places):
                if place["id"] == place_id:
                    # Preserva dados sensíveis
                    votes = place.get("votes", [])
                    visited = place.get("visited", False)
                    
                    # Atualiza RAM
                    places[i].update(updated_data)
                    
                    # Restaura campos protegidos
                    places[i]["id"] = place_id
                    places[i]["votes"] = votes
                    places[i]["visited"] = visited
                    found = True
                    break
            
            if found:
                PlaceService._persist(country, category)
                log.info(f"Local atualizado: {place_id}")
                return True
            return False
        except Exception as e:
            log.error(f"Erro update_place: {e}")
            return False

    @staticmethod
    async def delete_place(place_id, country_code, category):
        try:
            places = PlaceService._ensure_loaded(country_code, category)
            initial_len = len(places)
            
            # Filtra na RAM (Atualiza a referência da lista no cache)
            key = PlaceService._get_cache_key(country_code, category)
            PlaceService._cache[key] = [p for p in places if p["id"] != place_id]
            
            if len(PlaceService._cache[key]) < initial_len:
                PlaceService._persist(country_code, category)
                log.info(f"Local removido: {place_id}")
                return True
            return False
        except Exception as e:
            log.error(f"Erro delete_place: {e}")
            return False

    # --- SISTEMA DE VOTOS ---
    
    @staticmethod
    async def toggle_vote(place_id, country_code, category, user_id):
        """Votação Instantânea na RAM."""
        try:
            places = PlaceService._ensure_loaded(country_code, category)
            changed = False
            
            for place in places:
                if place["id"] == place_id:
                    votes = place.get("votes", [])
                    if user_id in votes:
                        votes.remove(user_id)
                    else:
                        votes.append(user_id)
                    place["votes"] = votes
                    changed = True
                    break
            
            if changed:
                # Fire & Forget na persistência (não precisamos esperar o disco para retornar true na UI)
                PlaceService._persist(country_code, category)
                return True
            return False
        except Exception as e:
            log.error(f"Erro toggle_vote: {e}")
            return False