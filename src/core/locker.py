# ARQUIVO: src/core/locker.py
import threading
from contextlib import contextmanager
import time

# Lock global para operações de escrita em JSON
# Isso garante que apenas uma thread do servidor escreva nos arquivos por vez
_json_lock = threading.Lock()

@contextmanager
def file_lock(timeout=10):
    """
    Context manager para garantir acesso exclusivo a arquivos críticos.
    Uso:
        with file_lock():
            json.dump(...)
    """
    # Tenta adquirir o cadeado. Se demorar mais que 'timeout', desiste para não travar o server.
    locked = _json_lock.acquire(timeout=timeout)
    try:
        if not locked:
            print("⚠️ AVISO CRÍTICO: Timeout ao tentar adquirir Lock de arquivo. Possível gargalo de I/O.")
        yield locked
    finally:
        if locked:
            _json_lock.release()