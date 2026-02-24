import time
import functools
import asyncio
from src.core.logger import get_logger, TripHubLogger

logger = get_logger("Profiler")

# Lista de funções repetitivas que NÃO DEVEM poluir o log.
# Elas rodarão silenciosamente no background.
IGNORE_SPAM = {
    "get_oracle_data", "get_config", "update_presence", 
    "get_profiles", "get_unread_count", "get_notifications",
    "get_places", "has_read", "get_checklist", "get_flights",
    "save_config"
}

def track_execution(threshold=1.0):
    """
    Decorator para medir tempo de execução.
    Se a função for spam de background, ela é ignorada do log para manter o terminal limpo.
    """
    def decorator(func):
        is_spam = func.__name__ in IGNORE_SPAM

        @functools.wraps(func)
        async def wrapper_async(*args, **kwargs):
            if is_spam:
                # Se for função de background, ignora totalmente os prints
                return await func(*args, **kwargs)
                
            level = TripHubLogger.get_monitoring_level()
            start_time = time.perf_counter()

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
                if level == "FULL":
                    logger.debug(f"[EXIT] {func.__name__} executou em {elapsed:.4f}s")
                elif level == "BASIC" and elapsed > threshold:
                    logger.warning(f"[SLOW] {func.__name__} demorou {elapsed:.4f}s (Limite: {threshold}s)")

        @functools.wraps(func)
        def wrapper_sync(*args, **kwargs):
            if is_spam:
                return func(*args, **kwargs)
                
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
                elif level == "BASIC" and elapsed > threshold:
                    logger.warning(f"[SLOW] {func.__name__} demorou {elapsed:.4f}s (Limite: {threshold}s)")

        if asyncio.iscoroutinefunction(func):
            return wrapper_async
        return wrapper_sync
    return decorator

monitor = track_execution