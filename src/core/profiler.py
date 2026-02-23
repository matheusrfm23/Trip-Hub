import time
import functools
import asyncio
from src.core.logger import get_logger

logger = get_logger("Profiler")

def monitor(threshold=1.0):
    """
    Decorator para medir tempo de execução de funções.
    Se demorar mais que 'threshold' segundos, emite um WARN.
    Se for síncrona, mede com time.perf_counter.
    Se for assíncrona, mede com await.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper_async(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"[CRASH] {func.__name__} falhou: {str(e)}", exc_info=True)
                raise e
            finally:
                elapsed = time.perf_counter() - start_time
                if elapsed > threshold:
                    logger.warning(f"[SLOW] {func.__name__} demorou {elapsed:.4f}s (Limite: {threshold}s)")
                else:
                    logger.debug(f"[PERF] {func.__name__} executou em {elapsed:.4f}s")

        @functools.wraps(func)
        def wrapper_sync(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"[CRASH] {func.__name__} falhou: {str(e)}", exc_info=True)
                raise e
            finally:
                elapsed = time.perf_counter() - start_time
                if elapsed > threshold:
                    logger.warning(f"[SLOW] {func.__name__} demorou {elapsed:.4f}s (Limite: {threshold}s)")
                else:
                    logger.debug(f"[PERF] {func.__name__} executou em {elapsed:.4f}s")

        if asyncio.iscoroutinefunction(func):
            return wrapper_async
        return wrapper_sync
    return decorator
