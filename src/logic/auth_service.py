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
    # Caminho do arquivo de dados principal (JSON)
    FILE_PATH = os.path.join("assets", "data", "profiles.json")

    # [REMOVIDO] CACHE_PATH = os.path.join("assets", "data", "cache.json")
    # [REMOVIDO] _cache_profiles (Variável Global)
    # [REMOVIDO] _cache_map (Variável Global)

    # PIN Mestre para operações administrativas
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
    def _init_db(cls):
        """Garante que o arquivo físico existe e contém uma lista vazia se necessário."""
        os.makedirs(os.path.dirname(cls.FILE_PATH), exist_ok=True)
        if not os.path.exists(cls.FILE_PATH):
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=4, ensure_ascii=False)

    @classmethod
    def _read_from_disk(cls):
        """
        Lê os perfis DIRETAMENTE do disco a cada chamada.
        Isso garante que em um ambiente multi-thread/multi-processo,
        sempre tenhamos o dado mais recente e isolado.
        """
        cls._init_db()
        try:
            # Leitura pode ser feita sem lock SE assumirmos que a escrita é atômica,
            # mas para garantir consistência absoluta, podemos usar lock ou confiar na atomicidade do OS.
            # Aqui, para leitura massiva, vamos ler direto para não travar o I/O.
            with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Erro ao ler perfis do disco: {e}")
            return []

    @classmethod
    def _write_to_disk(cls, profiles):
        """
        Escreve a lista completa de perfis no disco de forma segura.
        """
        try:
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(profiles, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            log.critical(f"ERRO CRÍTICO AO SALVAR PERFIS: {e}")
            return False

    @classmethod
    @monitor(threshold=2.0) 
    async def perform_integrity_check(cls):
        """Orquestrador de limpeza de dados"""
        log.info("Iniciando Verificação de Integridade dos Dados...")
        
        profiles = cls._read_from_disk()
        valid_ids = [str(p["id"]) for p in profiles]
        
        # Limpezas externas (Services dependentes)
        FlightService.clean_orphaned_flights(valid_ids)
        await FinanceService.clean_orphaned_finances(valid_ids)
        
        log.info(f"Verificação Concluída. {len(valid_ids)} perfis ativos.")

    @classmethod
    async def get_profiles(cls):
        """Retorna todos os perfis (Leitura fresca do disco)."""
        return cls._read_from_disk()

    @classmethod
    async def get_user_by_id(cls, user_id):
        """
        Busca usuário por ID iterando a lista do disco.
        Sem cache global para evitar vazamento de estado entre sessões.
        """
        profiles = cls._read_from_disk()
        for p in profiles:
            if str(p["id"]) == str(user_id):
                return p
        return None

    @classmethod
    @monitor(threshold=0.5)
    async def login(cls, user_id, pin):
        """
        Login validado contra o disco.
        Retorna o objeto do usuário se sucesso, ou None.
        """
        user = await cls.get_user_by_id(user_id)
        
        if user and str(user.get("pin")) == str(pin):
            log.info(f"Login realizado com sucesso: {user['name']}")
            return user
            
        log.warning(f"Falha de login para ID: {user_id}")
        return None

    @classmethod
    @monitor(threshold=1.0)
    async def create_profile(cls, name, pin):
        """
        Cria novo perfil de forma atômica (Read-Modify-Write protegido).
        """
        try:
            log.info(f"Tentando criar perfil: {name}")
            
            # BLOCO CRÍTICO: Read -> Modify -> Write deve ser atômico
            # Usamos o lock aqui para evitar que dois admins criem usuários ao mesmo tempo e um sobrescreva o outro.
            with file_lock():
                profiles = cls._read_from_disk() # Lê estado atual

                role = "ADMIN" if len(profiles) == 0 else "USER"

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

                profiles.append(new_user)

                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(profiles, f, indent=4, ensure_ascii=False)
            
            log.info(f"Perfil criado: {name} ({new_user['id']})")
            return True
        except Exception as e:
            log.error(f"Erro crítico ao criar perfil: {e}")
            return False

    @classmethod
    @monitor(threshold=0.5)
    async def update_profile_general(cls, profile_id, updates):
        """Atualiza campos gerais do perfil."""
        try:
            with file_lock():
                profiles = cls._read_from_disk()
                found = False
                
                for i, p in enumerate(profiles):
                    if str(p["id"]) == str(profile_id):
                        profiles[i].update(updates)
                        found = True
                        break

                if found:
                    with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(profiles, f, indent=4, ensure_ascii=False)
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
        Atualiza 'visto por último', localização e mensagem de status.
        Agora fazemos isso diretamente no disco para garantir persistência real.
        """
        try:
            # Otimização: Se for apenas heartbeat e o sistema estiver sob carga,
            # poderíamos pular ou usar um cache volátil (Redis), mas mantendo simples e seguro:
            
            with file_lock():
                profiles = cls._read_from_disk()
                found = False
                
                for i, p in enumerate(profiles):
                    if str(p["id"]) == str(user_id):
                        profiles[i]["last_seen"] = time.time()
                        if location is not None:
                            profiles[i]["last_location"] = location
                        if status_msg is not None:
                            profiles[i]["status_msg"] = status_msg
                        found = True
                        break
                
                if found:
                    with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(profiles, f, indent=4, ensure_ascii=False)
                    return True

            return False
        except Exception as e:
            return False

    @classmethod
    @monitor(threshold=1.0)
    async def delete_profile(cls, profile_id):
        try:
            log.warning(f"Solicitação de exclusão de perfil: {profile_id}")
            
            with file_lock():
                profiles = cls._read_from_disk()
                initial_len = len(profiles)

                # Filtra a lista removendo o ID alvo
                new_profiles = [p for p in profiles if str(p["id"]) != str(profile_id)]

                if len(new_profiles) < initial_len:
                    with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(new_profiles, f, indent=4, ensure_ascii=False)
            
            # Limpeza de dados órfãos (voos, finanças) após a exclusão bem-sucedida
            await cls.perform_integrity_check()
            
            log.info(f"Perfil excluído com sucesso: {profile_id}")
            return True
        except Exception as e:
            log.critical(f"Erro Crítico ao Deletar: {e}")
            return False

    # [REMOVIDO] Métodos de cache de sessão (save_cached_login, get_cached_login, clear_cached_login)
    # A responsabilidade de manter a sessão agora é inteiramente do Client Side (Flet Storage)
