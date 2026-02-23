import logging
import colorlog
import os
from logging.handlers import RotatingFileHandler

# Cria pasta de logs se não existir
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_logger(name):
    """
    Retorna um logger configurado com cores para o terminal e arquivo rotativo.
    """
    logger = logging.getLogger(name)
    
    # Evita duplicidade de logs se chamar a função várias vezes
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)

    # --- FORMATO ---
    log_format = "%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | %(cyan)s%(name)s%(reset)s | %(message)s"
    date_format = "%H:%M:%S"

    # --- HANDLER 1: TERMINAL (Colorido) ---
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(colorlog.ColoredFormatter(
        log_format,
        datefmt=date_format,
        log_colors={
            'DEBUG': 'blue',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red,bg_white',
        }
    ))
    logger.addHandler(stream_handler)

    # --- HANDLER 2: ARQUIVO (Completo e Rotativo) ---
    # Salva em arquivo, cria um novo quando chegar a 5MB, mantém os últimos 3
    file_handler = RotatingFileHandler(
        f"{LOG_DIR}/app.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    ))
    # No arquivo gravamos apenas de INFO para cima (ou DEBUG se quiser tudo)
    file_handler.setLevel(logging.INFO) 
    logger.addHandler(file_handler)

    return logger