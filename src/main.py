import logging
import os
import threading
import webbrowser
import time
import flet as ft

from src.core.logger import get_logger
from src.core.config import AppConfig, ASSETS_DIR, UPLOAD_ABS_PATH, MEU_IP, PORTA
from src.core.router import Router
from src.logic.auth_service import AuthService
from src.data.database import Database
from src.ui.components.modal_preview import ModalPreview

logger = get_logger("TripHub.Main")

async def main(page: ft.Page):
    logger.info(">>> STARTUP: Iniciando Trip Hub...")

    try:
        db = Database()
        db.initialize()
        logger.info("Banco de dados conectado e inicializado.")
    except Exception as e:
        logger.critical(f"FALHA CRÍTICA NO BANCO DE DADOS: {e}", exc_info=True)

    try:
        await AuthService.perform_integrity_check()
    except Exception as e:
        logger.error(f"Erro na verificação de integridade: {e}", exc_info=True)

    page.title = AppConfig.WINDOW_TITLE
    page.window_width = 400
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK
    page.padding = 0
    page.spacing = 0

    modal_preview = ModalPreview(page)
    modal_preview.register()
    page.modal_preview = modal_preview 

    router = Router(page)
    
    def window_event(e):
        if e.data == "resize": page.update()
    page.on_window_event = window_event

    initial_route = page.route if page.route and page.route != "/" else "/login"
    logger.info(f"Definindo rota inicial para: {initial_route}")
    
    await router.route_change(initial_route) 
    await page.push_route(initial_route)


def open_browser():
    """Abre o navegador perfeitamente no Localhost, não no 0.0.0.0"""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORTA}")


if __name__ == "__main__":
    is_docker = os.path.exists("/.dockerenv") or os.environ.get("ENVIRONMENT") == "production"

    print("\n" + "="*60)
    print(f"🚀 TRIP HUB SERVER")
    if is_docker:
        print(f"📡 MODO PRODUÇÃO (Docker/Oracle)")
        print(f"🌐 SERVIDOR ATIVO EM: http://0.0.0.0:{PORTA}")
    else:
        print(f"📡 MODO TESTE LOCAL (Wi-Fi Pronto)")
        print(f"💻 ACESSO LOCAL (Neste PC):   http://localhost:{PORTA}")
        print(f"📱 ACESSO PELO CELULAR:       http://{MEU_IP}:{PORTA}")
        # Dispara thread para abrir no navegador local sem bugar
        threading.Thread(target=open_browser, daemon=True).start()
    print("="*60 + "\n")
    
    # ATENÇÃO: Substituído ft.app() que gera Warning por ft.run()
    # view=None impede o Flet de tentar abrir "http://0.0.0.0" sozinho
    ft.run(
        target=main, 
        assets_dir=ASSETS_DIR,
        upload_dir=UPLOAD_ABS_PATH,
        port=PORTA,
        host="0.0.0.0",
        view=None 
    )