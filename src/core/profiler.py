# ARQUIVO: src/core/profiler.py
# CHANGE LOG:
# - Código original restaurado mantendo a lógica dinâmica de níveis de monitoramento (FULL, BASIC, ERROR_ONLY).

import time
import functools
import asyncio
from src.core.logger import get_logger, TripHubLogger

logger = get_logger("Profiler")

def track_execution(threshold=1.0):
    """
    Decorator para medir tempo de execução.
    Se MONITORING_LEVEL == FULL: Loga argumentos e tempo.
    Se MONITORING_LEVEL == BASIC: Loga apenas tempo se exceder threshold.
    Se MONITORING_LEVEL == ERROR_ONLY: Loga apenas se der erro (exceção).
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper_async(*args, **kwargs):
            level = TripHubLogger.get_monitoring_level()
            start_time = time.perf_counter()

            # Log de entrada (FULL)
            if level == "FULL":
                logger.debug(f"[ENTER] {func.__name__} args={args} kwargs={kwargs}")

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"[CRASH] {func.__name__} falhou: {str(e)}", exc_info=True)
                raise e
            finally:
                elapsed = time.perf_counter() - start_time

                # Log de saída/performance
                if level == "FULL":
                    logger.debug(f"[EXIT] {func.__name__} executou em {elapsed:.4f}s")
                elif level == "BASIC":
                    if elapsed > threshold:
                        logger.warning(f"[SLOW] {func.__name__} demorou {elapsed:.4f}s (Limite: {threshold}s)")

        @functools.wraps(func)
        def wrapper_sync(*args, **kwargs):
            level = TripHubLogger.get_monitoring_level()
            start_time = time.perf_counter()

            if level == "FULL":
                logger.debug(f"[ENTER] {func.__name__} args={args} kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"[CRASH] {func.__name__} falhou: {str(e)}", exc_info=True)
                raise e
            finally:
                elapsed = time.perf_counter() - start_time

                if level == "FULL":
                    logger.debug(f"[EXIT] {func.__name__} executou em {elapsed:.4f}s")
                elif level == "BASIC":
                    if elapsed > threshold:
                        logger.warning(f"[SLOW] {func.__name__} demorou {elapsed:.4f}s (Limite: {threshold}s)")

        if asyncio.iscoroutinefunction(func):
            return wrapper_async
        return wrapper_sync
    return decorator

# Alias para compatibilidade se necessário, mas o padrão agora é @track_execution
monitor = track_execution