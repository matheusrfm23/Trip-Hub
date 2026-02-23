# ARQUIVO: src/logic/notification_service.py
import json
import os
import uuid
from datetime import datetime
from src.core.locker import file_lock  # <--- IMPORTANTE: O Cadeado

class NotificationService:
    FILE_PATH = os.path.join("assets", "data", "notifications.json")

    @classmethod
    def _init_db(cls):
        os.makedirs(os.path.dirname(cls.FILE_PATH), exist_ok=True)
        if not os.path.exists(cls.FILE_PATH):
            with file_lock():
                with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=4, ensure_ascii=False)

    @classmethod
    def _read_file_internal(cls):
        """Lê o arquivo sem lock (deve ser chamado dentro de um lock ou para leitura simples)"""
        cls._init_db()
        try:
            with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []

    @classmethod
    def _write_file_internal(cls, data):
        """Escreve no arquivo sem lock (o caller deve garantir o lock)"""
        try:
            with open(cls.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar notificações: {e}")

    @classmethod
    async def get_notifications(cls, user_id):
        # Leitura isolada não precisa de lock estrito, mas init_db garante que arquivo existe
        all_notifs = cls._read_file_internal()
        
        my_notifs = [
            n for n in all_notifs 
            if n["target_id"] == "ALL" or str(n["target_id"]) == str(user_id)
        ]
        # Ordena: Mais recentes primeiro
        my_notifs.sort(key=lambda x: x["timestamp"], reverse=True)
        return my_notifs

    @classmethod
    async def get_unread_count(cls, user_id):
        notifs = await cls.get_notifications(user_id)
        count = 0
        for n in notifs:
            if str(user_id) not in n.get("read_by", []):
                count += 1
        return count

    # --- MÉTODOS DE ESCRITA (BLINDADOS) ---

    @classmethod
    async def mark_as_read(cls, notif_id, user_id):
        # Lock envolve Leitura + Modificação + Escrita para evitar conflito
        with file_lock():
            all_notifs = cls._read_file_internal()
            changed = False
            for n in all_notifs:
                if n["id"] == notif_id:
                    if "read_by" not in n: n["read_by"] = []
                    if str(user_id) not in n["read_by"]:
                        n["read_by"].append(str(user_id))
                        changed = True
                    break
            
            if changed:
                cls._write_file_internal(all_notifs)

    @classmethod
    async def mark_all_read(cls, user_id):
        with file_lock():
            all_notifs = cls._read_file_internal()
            changed = False
            for n in all_notifs:
                if n["target_id"] == "ALL" or str(n["target_id"]) == str(user_id):
                    if "read_by" not in n: n["read_by"] = []
                    if str(user_id) not in n["read_by"]:
                        n["read_by"].append(str(user_id))
                        changed = True
            
            if changed:
                cls._write_file_internal(all_notifs)

    @classmethod
    async def send_notification(cls, sender_name, target_id, title, message, type="info"):
        with file_lock():
            all_notifs = cls._read_file_internal()
            
            new_notif = {
                "id": str(uuid.uuid4()),
                "sender": sender_name,
                "target_id": target_id,
                "title": title,
                "message": message,
                "type": type,
                "timestamp": datetime.now().strftime("%d/%m %H:%M"),
                "read_by": []
            }
            all_notifs.append(new_notif)
            
            cls._write_file_internal(all_notifs)
        return True

    @classmethod
    async def clear_all(cls):
        """Apaga TODAS as notificações do sistema (Função Admin)."""
        with file_lock():
            cls._write_file_internal([]) 
        return True

    @classmethod
    async def delete_notification(cls, notif_id):
        with file_lock():
            all_notifs = cls._read_file_internal()
            new_list = [n for n in all_notifs if n["id"] != notif_id]
            cls._write_file_internal(new_list)
        return True