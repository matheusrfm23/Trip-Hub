import json
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Diretório de Logs
LOG_DIR = "logs"
CONFIG_FILE = "log_config.json"

class TripHubLogger:
    _instance = None
    _config = {
        "console_enabled": True,
        "file_enabled": True,
        "retention_days": 7,
        "monitoring_level": "BASIC"  # ERROR_ONLY, BASIC, FULL
    }

    LEVEL_MAP = {
        "ERROR_ONLY": logging.ERROR,
        "BASIC": logging.INFO,
        "FULL": logging.DEBUG
    }

    @classmethod
    def get_logger(cls, name="TripHub"):
        """Retorna uma instância configurada de Logger"""
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        cls._load_config()

        logger = logging.getLogger(name)

        # Define o nível do logger baseado na configuração
        level_name = cls._config.get("monitoring_level", "BASIC").upper()
        log_level = cls.LEVEL_MAP.get(level_name, logging.INFO)
        logger.setLevel(log_level)

        # Evita duplicação de handlers se get_logger for chamado várias vezes
        if logger.hasHandlers():
            logger.handlers.clear()

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. Handler de Console (Terminal)
        if cls._config.get("console_enabled"):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # 2. Handler de Arquivo (Rotação Diária)
        if cls._config.get("file_enabled"):
            filename = os.path.join(LOG_DIR, "app.log")
            # Roda a cada meia-noite (midnight), mantém backup por X dias (backupCount)
            file_handler = TimedRotatingFileHandler(
                filename,
                when="midnight",
                interval=1,
                backupCount=cls._config.get("retention_days", 7),
                encoding="utf-8"
            )
            # Sufixo do arquivo rotacionado: app_2024-05-25.log
            file_handler.suffix = "%Y-%m-%d.log"
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @classmethod
    def _load_config(cls):
        """Carrega configuração do arquivo JSON se existir"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    cls._config.update(json.load(f))
            except Exception as e:
                print(f"Erro ao carregar log_config.json: {e}")

    @classmethod
    def update_config(cls, new_config):
        """Atualiza a configuração em tempo real e salva no disco"""
        cls._config.update(new_config)
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(cls._config, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar log_config.json: {e}")

    @classmethod
    def get_monitoring_level(cls):
        return cls._config.get("monitoring_level", "BASIC").upper()

# Função helper global para fácil importação
def get_logger(name="TripHub"):
    return TripHubLogger.get_logger(name)
