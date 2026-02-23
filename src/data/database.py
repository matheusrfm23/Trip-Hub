# ARQUIVO: src/data/database.py
import sqlite3
import os

class Database:
    DB_DIR = "assets/data"
    DB_NAME = "triphub.db"

    @classmethod
    def get_connection(cls):
        if not os.path.exists(cls.DB_DIR):
            os.makedirs(cls.DB_DIR)
        
        db_path = os.path.join(cls.DB_DIR, cls.DB_NAME)
        
        # check_same_thread=False é necessário para Flet/FastAPI (multi-usuário)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome (ex: row['id'])
        
        # --- BLINDAGEM DE CONCORRÊNCIA (MEDIDA 1) ---
        # Ativa o modo Write-Ahead Logging: Permite leitura e escrita simultâneas
        conn.execute("PRAGMA journal_mode=WAL;") 
        
        # Sincronização NORMAL: Seguro contra falhas de energia, mas muito mais rápido que o padrão
        conn.execute("PRAGMA synchronous=NORMAL;") 
        
        # Timeout: Se o banco estiver ocupado, espera 5 segundos antes de dar erro
        # Isso evita travamentos quando muitos usuários clicam juntos
        conn.execute("PRAGMA busy_timeout=5000;") 
        # ---------------------------------------------
        
        return conn

    @classmethod
    def initialize(cls):
        """Cria as tabelas necessárias se não existirem"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # Tabela de Finanças
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
                involved_ids TEXT,  -- JSON String
                contested_by TEXT   -- JSON String
            )
        ''')
        
        # Tabela de Voos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flights (
                id TEXT PRIMARY KEY,
                locator TEXT,
                passenger TEXT,
                details TEXT
            )
        ''')

        # Tabela de Mensagens (Chat)
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
        # Índices para performance do chat
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sender ON messages(sender_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_receiver ON messages(receiver_id)')
        
        conn.commit()
        conn.close()

# Inicializa ao importar para garantir que o arquivo .db e as tabelas existam
Database.initialize()