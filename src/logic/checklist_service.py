# ARQUIVO: src/logic/checklist_service.py
import json
import os
from src.core.locker import file_lock  # <--- IMPORTANTE: O Cadeado

class ChecklistService:
    FILE_PATH = "assets/data/checklists.json"

    @staticmethod
    def _ensure_file_exists():
        if not os.path.exists(ChecklistService.FILE_PATH):
            os.makedirs(os.path.dirname(ChecklistService.FILE_PATH), exist_ok=True)
            # Proteção na criação
            with file_lock():
                with open(ChecklistService.FILE_PATH, "w") as f:
                    json.dump({}, f)

    @staticmethod
    def get_checklist(user_id):
        """Leitura segura (sem lock bloqueante, mas garantindo existência)"""
        ChecklistService._ensure_file_exists()
        try:
            with open(ChecklistService.FILE_PATH, "r") as f:
                data = json.load(f)
            return data.get(str(user_id), [])
        except:
            return []

    @staticmethod
    def save_checklist(user_id, items):
        """Salva a checklist do usuário preservando as dos outros."""
        ChecklistService._ensure_file_exists()
        try:
            # BLINDAGEM: Bloqueia o arquivo para ler E escrever
            with file_lock():
                # 1. Lê o estado atual
                with open(ChecklistService.FILE_PATH, "r") as f:
                    data = json.load(f)
                
                # 2. Atualiza apenas este usuário
                data[str(user_id)] = items
                
                # 3. Salva tudo de volta
                with open(ChecklistService.FILE_PATH, "w") as f:
                    json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Erro ao salvar checklist: {e}")
            return False

    @staticmethod
    def reset_checks(user_id):
        """Zera os 'checks' mas mantém os itens (para a viagem de volta)"""
        # Pega a lista atual
        items = ChecklistService.get_checklist(user_id)
        
        # Modifica em memória
        for item in items:
            item["checked"] = False
            
        # Salva (o método save_checklist já tem o lock, então é seguro)
        return ChecklistService.save_checklist(user_id, items)