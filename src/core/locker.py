# ARQUIVO: src/core/locker.py
# CHANGE LOG:
# - Corrigida falha de segurança onde operações continuavam mesmo se o lock falhasse.
# - Lançamento explícito de TimeoutError para impedir corrupção de dados por concorrência simultânea.

import threading
from contextlib import contextmanager

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
    
    if not locked:
        print("⚠️ ERRO CRÍTICO: Timeout ao tentar adquirir Lock de arquivo. Operação abortada para evitar corrupção.")
        raise TimeoutError("Não foi possível adquirir acesso exclusivo ao arquivo.")
        
    try:
        yield locked
    finally:
        _json_lock.release()