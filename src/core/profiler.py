# ARQUIVO: src/core/profiler.py
# CHANGE LOG:
# - Remoção do print verboso de args/kwargs.
# - Inclusão de novos spams detectados (save_checklist, perform_integrity_check).
# - Resolução segura do nome da função mascarada.

import time
import functools
import asyncio
import json
import os
from src.core.logger import get_logger, TripHubLogger

logger = get_logger("Profiler")

IGNORE_SPAM = [
    "get_oracle_data", "get_config", "update_presence", 
    "get_profiles", "get_unread_count", "get_notifications",
    "get_places", "has_read", "get_checklist", "get_flights",
    "save_config", "update_rates", "save_checklist", "perform_integrity_check"
]

def is_polling_enabled():
    try:
        if os.path.exists("log_config.json"):
            with open("log_config.json", "r") as f:
                return json.load(f).get("show_polling_logs", False)
    except:
        pass
    return False

def track_execution(threshold=1.0):
    def decorator(func):
        func_name = getattr(func, "__name__", str(func))
        is_spam = any(spam in func_name for spam in IGNORE_SPAM)

        @functools.wraps(func)
        async def wrapper_async(*args, **kwargs):
            if is_spam and not is_polling_enabled():
                return await func(*args, **kwargs)
                
            level = TripHubLogger.get_monitoring_level()
            start_time = time.perf_counter()

            if level == "FULL":
                logger.debug(f"[ENTER] {func_name}")

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[CRASH] {func_name} falhou: {str(e)}", exc_info=True)
                raise e
            finally:
                elapsed = time.perf_counter() - start_time
                if level == "FULL":
                    logger.debug(f"[EXIT] {func_name} executou em {elapsed:.4f}s")
                elif level == "BASIC" and elapsed > threshold:
                    logger.warning(f"[SLOW] {func_name} demorou {elapsed:.4f}s (Limite: {threshold}s)")

        @functools.wraps(func)
        def wrapper_sync(*args, **kwargs):
            if is_spam and not is_polling_enabled():
                return func(*args, **kwargs)
                
            level = TripHubLogger.get_monitoring_level()
            start_time = time.perf_counter()

            if level == "FULL":
                logger.debug(f"[ENTER] {func_name}")

            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[CRASH] {func_name} falhou: {str(e)}", exc_info=True)
                raise e
            finally:
                elapsed = time.perf_counter() - start_time
                if level == "FULL":
                    logger.debug(f"[EXIT] {func_name} executou em {elapsed:.4f}s")
                elif level == "BASIC" and elapsed > threshold:
                    logger.warning(f"[SLOW] {func_name} demorou {elapsed:.4f}s (Limite: {threshold}s)")

        if asyncio.iscoroutinefunction(func):
            return wrapper_async
        return wrapper_sync
    return decorator

monitor = track_execution