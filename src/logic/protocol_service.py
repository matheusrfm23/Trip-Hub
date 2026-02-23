# ARQUIVO: src/logic/protocol_service.py
import json
import os
from src.core.locker import file_lock  # <--- IMPORTANTE: O Cadeado

class ProtocolService:
    # Arquivo onde salvaremos quem já leu
    FILE_PATH = "assets/data/protocol_status.json"

    @staticmethod
    def _ensure_file_exists():
        """Garante que o arquivo JSON exista"""
        if not os.path.exists(ProtocolService.FILE_PATH):
            os.makedirs(os.path.dirname(ProtocolService.FILE_PATH), exist_ok=True)
            # Proteção na criação
            with file_lock():
                with open(ProtocolService.FILE_PATH, "w") as f:
                    json.dump({}, f)

    @staticmethod
    def has_read(user_id):
        """Verifica se o usuário já leu (Leitura segura)"""
        ProtocolService._ensure_file_exists()
        try:
            with open(ProtocolService.FILE_PATH, "r") as f:
                data = json.load(f)
            # Retorna True se o ID estiver lá e for True
            return data.get(str(user_id), False)
        except:
            return False

    @staticmethod
    def mark_as_read(user_id):
        """Salva que o usuário leu com proteção contra conflitos"""
        ProtocolService._ensure_file_exists()
        try:
            # BLINDAGEM: Bloqueia para ler E escrever
            with file_lock():
                # 1. Lê o atual
                with open(ProtocolService.FILE_PATH, "r") as f:
                    data = json.load(f)
                
                # 2. Atualiza
                data[str(user_id)] = True
                
                # 3. Salva
                with open(ProtocolService.FILE_PATH, "w") as f:
                    json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Erro ao salvar protocolo: {e}")
            return False