# ARQUIVO: src/data/database.py
# CHANGE LOG:
# - Importação do DATA_DIR de src.core.config para evitar caminhos relativos instáveis.
# - Atualização de DB_DIR para utilizar a constante global segura do projeto.

import sqlite3
import os
import json
import logging
import glob
import uuid

# Importando o caminho absoluto e seguro definido na configuração base
from src.core.config import DATA_DIR

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("Database")

class Database:
    # Utilizando o caminho absoluto para evitar bancos de dados fantasmas em pastas incorretas
    DB_DIR = DATA_DIR
    DB_NAME = "triphub.db"

    # Arquivos JSON mapeados para migração
    JSON_FILES = {
        "users": "profiles.json",
        "flights": "flights.json",
        "notifications": "notifications.json",
        "checklists": "checklists.json",
        "protocol_reads": "protocol_status.json",
        "banner_config": "banner_config.json",
        "schedule": "schedule.json"
    }

    @classmethod
    def get_connection(cls):
        if not os.path.exists(cls.DB_DIR):
            os.makedirs(cls.DB_DIR)
        
        db_path = os.path.join(cls.DB_DIR, cls.DB_NAME)
        
        # check_same_thread=False é necessário para Flet/FastAPI (multi-usuário)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
        
        # --- BLINDAGEM DE CONCORRÊNCIA (MEDIDA 1) ---
        conn.execute("PRAGMA journal_mode=WAL;") 
        conn.execute("PRAGMA synchronous=NORMAL;") 
        conn.execute("PRAGMA busy_timeout=5000;") 
        # ---------------------------------------------
        
        return conn

    @classmethod
    def initialize(cls):
        """Cria as tabelas e roda migração se necessário."""
        log.info("Inicializando Banco de Dados...")
        cls._create_tables()
        cls._migrate_legacy_jsons()

    @classmethod
    def _create_tables(cls):
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # 1. Tabela Users (profiles.json)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT,
                pin TEXT,
                avatar TEXT,
                passport TEXT,
                cpf TEXT,
                rg TEXT,
                privacy TEXT,       -- JSON: {passport: bool, medical: bool}
                contact TEXT,       -- JSON: {phone, email, ...}
                medical TEXT,       -- JSON: {blood_type, allergies, ...}
                last_seen REAL,
                last_location TEXT, -- JSON/String
                status_msg TEXT
            )
        ''')

        # 2. Tabela Flights (flights.json)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flights (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                locator TEXT,
                passenger TEXT,
                details TEXT        -- JSON: Resto dos dados
            )
        ''')

        # 3. Tabela Places (arquivos br_hotel.json, etc)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS places (
                id TEXT PRIMARY KEY,
                country TEXT,       
                category TEXT,
                name TEXT,
                description TEXT,
                lat REAL,
                lon REAL,
                maps_link TEXT,
                visited INTEGER DEFAULT 0,
                votes TEXT,         -- JSON Array: ["user_id1", "user_id2"]
                extra_data TEXT,    -- JSON: {address, phone, ...}
                added_by TEXT
            )
        ''')

        # 4. Tabela Banner Config (banner_config.json)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS banner_config (
                id INTEGER PRIMARY KEY CHECK (id = 1), -- Garante única linha
                mode TEXT,
                theme TEXT,
                dynamic_theme INTEGER,
                manual_text TEXT,
                manual_advice TEXT,
                start_date TEXT,
                target_date TEXT,
                target_location TEXT, -- JSON: {lat, lon, name}
                show_timeline INTEGER,
                show_weather INTEGER,
                show_currency INTEGER,
                show_advice INTEGER,
                alert_enabled INTEGER,
                alert_target REAL
            )
        ''')

        # 5. Tabela Notifications (notifications.json)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                sender TEXT,
                target_id TEXT,
                title TEXT,
                message TEXT,
                type TEXT,
                timestamp TEXT,
                read_by TEXT        -- JSON Array: ["user_id1", ...]
            )
        ''')

        # 6. Tabela Checklists (checklists.json)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checklists (
                user_id TEXT PRIMARY KEY,
                items TEXT          -- JSON Array: [{text, checked}, ...]
            )
        ''')

        # 7. Tabela Protocol Reads (protocol_status.json)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS protocol_reads (
                user_id TEXT PRIMARY KEY,
                has_read INTEGER DEFAULT 0
            )
        ''')

        # 8. Tabela Schedule (schedule.json)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id TEXT PRIMARY KEY,
                title TEXT,
                start TEXT,
                end TEXT,
                description TEXT,
                type TEXT
            )
        ''')

        # --- TABELAS LEGADO (Mantidas) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                date TEXT,
                description TEXT,
                amount REAL,
                currency TEXT,
                amount_brl REAL,
                category TEXT,
                payer_id TEXT,
                payer_name TEXT,
                involved_ids TEXT,
                contested_by TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                is_read INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sender ON messages(sender_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_receiver ON messages(receiver_id)')
        
        conn.commit()
        conn.close()

    @classmethod
    def _migrate_legacy_jsons(cls):
        """Lê JSONs antigos, insere no SQLite e renomeia para .bak de forma transacional."""
        conn = cls.get_connection()
        cursor = conn.cursor()

        files_to_rename = []

        try:
            # 1. Migrar Users
            files_to_rename.extend(cls._migrate_file(cursor, "users", cls.JSON_FILES["users"], cls._parse_user))

            # 2. Migrar Flights
            files_to_rename.extend(cls._migrate_file(cursor, "flights", cls.JSON_FILES["flights"], cls._parse_flight))

            # 3. Migrar Notifications
            files_to_rename.extend(cls._migrate_file(cursor, "notifications", cls.JSON_FILES["notifications"], cls._parse_notification))

            # 4. Migrar Checklists
            files_to_rename.extend(cls._migrate_file(cursor, "checklists", cls.JSON_FILES["checklists"], cls._parse_checklist))

            # 5. Migrar Protocol Reads
            files_to_rename.extend(cls._migrate_file(cursor, "protocol_reads", cls.JSON_FILES["protocol_reads"], cls._parse_protocol))

            # 6. Migrar Banner Config
            files_to_rename.extend(cls._migrate_single_object(cursor, "banner_config", cls.JSON_FILES["banner_config"], cls._parse_banner))

            # 7. Migrar Schedule
            files_to_rename.extend(cls._migrate_file(cursor, "schedule", cls.JSON_FILES["schedule"], cls._parse_schedule))

            # 8. Migrar Places (Padrão curinga *_*.json)
            files_to_rename.extend(cls._migrate_places(cursor))

            if files_to_rename:
                conn.commit()
                # Apenas renomeia se o commit foi bem sucedido
                for filepath in files_to_rename:
                    try:
                        os.replace(filepath, filepath + ".bak")
                        log.info(f"Arquivo renomeado: {os.path.basename(filepath)} -> .bak")
                    except OSError as e:
                        log.error(f"Erro ao renomear {filepath}: {e}")
            else:
                conn.commit() # Commit das tabelas vazias se necessário

        except Exception as e:
            log.error(f"Erro Crítico na Migração (Rollback): {e}")
            conn.rollback()
        finally:
            conn.close()

    @classmethod
    def _migrate_file(cls, cursor, table, filename, parser_func):
        filepath = os.path.join(cls.DB_DIR, filename)
        if not os.path.exists(filepath):
            return []

        log.info(f"Migrando {filename} para tabela {table}...")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    columns, values = parser_func(item)
                    placeholders = ", ".join(["?"] * len(values))
                    col_names = ", ".join(columns)
                    sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
            elif isinstance(data, dict):
                 for key, val in data.items():
                    columns, values = parser_func(key, val)
                    placeholders = ", ".join(["?"] * len(values))
                    col_names = ", ".join(columns)
                    sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"
                    cursor.execute(sql, values)

            return [filepath]

        except Exception as e:
            log.error(f"Falha ao processar {filename}: {e}")
            return []

    @classmethod
    def _migrate_single_object(cls, cursor, table, filename, parser_func):
        filepath = os.path.join(cls.DB_DIR, filename)
        if not os.path.exists(filepath):
            return []

        log.info(f"Migrando {filename} para tabela {table}...")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            columns, values = parser_func(data)
            placeholders = ", ".join(["?"] * len(values))
            col_names = ", ".join(columns)

            cursor.execute(f"DELETE FROM {table}")
            sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
            cursor.execute(sql, values)

            return [filepath]
        except Exception as e:
            log.error(f"Falha ao processar {filename}: {e}")
            return []

    @classmethod
    def _migrate_places(cls, cursor):
        pattern = os.path.join(cls.DB_DIR, "*_*.json")
        files = glob.glob(pattern)
        processed_files = []

        for filepath in files:
            filename = os.path.basename(filepath)
            if filename in cls.JSON_FILES.values(): continue
            if filename.endswith(".bak"): continue

            log.info(f"Migrando Places de {filename}...")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    places = json.load(f)

                for p in places:
                    columns, values = cls._parse_place(p)
                    placeholders = ", ".join(["?"] * len(values))
                    col_names = ", ".join(columns)
                    sql = f"INSERT OR IGNORE INTO places ({col_names}) VALUES ({placeholders})"
                    cursor.execute(sql, values)

                processed_files.append(filepath)
            except Exception as e:
                log.error(f"Erro ao migrar places {filename}: {e}")

        return processed_files

    @staticmethod
    def _parse_user(u):
        cols = ["id", "name", "role", "pin", "avatar", "passport", "cpf", "rg", "privacy", "contact", "medical", "last_seen", "last_location", "status_msg"]
        vals = [
            u.get("id"), u.get("name"), u.get("role"), u.get("pin"), u.get("avatar"),
            u.get("passport"), u.get("cpf"), u.get("rg"),
            json.dumps(u.get("privacy", {}), ensure_ascii=False),
            json.dumps(u.get("contact", {}), ensure_ascii=False),
            json.dumps(u.get("medical", {}), ensure_ascii=False),
            u.get("last_seen", 0),
            u.get("last_location") if isinstance(u.get("last_location"), str) else json.dumps(u.get("last_location"), ensure_ascii=False),
            u.get("status_msg")
        ]
        return cols, vals

    @staticmethod
    def _parse_flight(f):
        cols = ["id", "user_id", "locator", "passenger", "details"]
        main_keys = ["id", "user_id", "locator", "passenger"]
        details = {k: v for k, v in f.items() if k not in main_keys}

        vals = [
            f.get("id"), f.get("user_id"), f.get("locator"), f.get("passenger"),
            json.dumps(details, ensure_ascii=False)
        ]
        return cols, vals

    @staticmethod
    def _parse_notification(n):
        cols = ["id", "sender", "target_id", "title", "message", "type", "timestamp", "read_by"]
        vals = [
            n.get("id"), n.get("sender"), n.get("target_id"), n.get("title"), n.get("message"),
            n.get("type"), n.get("timestamp"), json.dumps(n.get("read_by", []), ensure_ascii=False)
        ]
        return cols, vals

    @staticmethod
    def _parse_checklist(user_id, items):
        cols = ["user_id", "items"]
        vals = [user_id, json.dumps(items, ensure_ascii=False)]
        return cols, vals

    @staticmethod
    def _parse_protocol(user_id, has_read):
        cols = ["user_id", "has_read"]
        vals = [user_id, 1 if has_read else 0]
        return cols, vals

    @staticmethod
    def _parse_banner(b):
        cols = ["id", "mode", "theme", "dynamic_theme", "manual_text", "manual_advice", "start_date", "target_date", "target_location", "show_timeline", "show_weather", "show_currency", "show_advice", "alert_enabled", "alert_target"]
        vals = [
            1, b.get("mode"), b.get("theme"), 1 if b.get("dynamic_theme") else 0,
            b.get("manual_text"), b.get("manual_advice"), b.get("start_date"), b.get("target_date"),
            json.dumps(b.get("target_location", {}), ensure_ascii=False),
            1 if b.get("show_timeline") else 0,
            1 if b.get("show_weather") else 0,
            1 if b.get("show_currency") else 0,
            1 if b.get("show_advice") else 0,
            1 if b.get("alert_enabled") else 0,
            b.get("alert_target", 0)
        ]
        return cols, vals

    @staticmethod
    def _parse_schedule(s):
        cols = ["id", "title", "start", "end", "description", "type"]
        vals = [
            s.get("id") or str(uuid.uuid4()),
            s.get("title"), s.get("start"), s.get("end"), s.get("description"), s.get("type", "event")
        ]
        return cols, vals

    @staticmethod
    def _parse_place(p):
        cols = ["id", "country", "category", "name", "description", "lat", "lon", "maps_link", "visited", "votes", "extra_data", "added_by"]

        main_keys = ["id", "country", "category", "name", "description", "lat", "lon", "maps_link", "visited", "votes", "added_by"]
        extra = {k: v for k, v in p.items() if k not in main_keys}

        vals = [
            p.get("id"), p.get("country"), p.get("category"), p.get("name"), p.get("description"),
            p.get("lat"), p.get("lon"), p.get("maps_link"),
            1 if p.get("visited") else 0,
            json.dumps(p.get("votes", []), ensure_ascii=False),
            json.dumps(extra, ensure_ascii=False),
            p.get("added_by")
        ]
        return cols, vals