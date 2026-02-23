import time
import functools
import asyncio
import traceback
from src.core.logger import get_logger

# Logger exclusivo para performance
perf_logger = get_logger("PERFORMANCE")

def monitor(threshold=0.5):
    """
    Decorator para monitorar tempo de execução e erros.
    threshold: Tempo máximo (segundos) antes de emitir um alerta de lentidão.
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            func_name = func.__name__
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                perf_logger.error(f"❌ ERRO em '{func_name}': {str(e)}")
                perf_logger.debug(traceback.format_exc()) # Loga o erro completo no arquivo
                raise e # Repassa o erro para o sistema tratar
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                
                if duration > threshold:
                    perf_logger.warning(f"🐢 LENTIDÃO: '{func_name}' levou {duration:.4f}s (Limite: {threshold}s)")
                else:
                    # Opcional: Descomente para ver tudo que roda
                    # perf_logger.debug(f"⚡ '{func_name}' executou em {duration:.4f}s")
                    pass

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            func_name = func.__name__
            try:
                return func(*args, **kwargs)
            except Exception as e:
                perf_logger.error(f"❌ ERRO em '{func_name}': {str(e)}")
                perf_logger.debug(traceback.format_exc())
                raise e
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                if duration > threshold:
                    perf_logger.warning(f"🐢 LENTIDÃO: '{func_name}' levou {duration:.4f}s")

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator