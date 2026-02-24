# ARQUIVO: src/main.py
# CHANGE LOG:
# - Implementado `view=None` na raiz do ft.run para impedir o Flet de abrir URLs estranhas.
# - Roteamento web embutido em background para garantir que abra EXATAMENTE o localhost:8000.
# - Atualização obrigatória para ft.run (encerra o DeprecationWarning no terminal).

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

def open_browser_delayed(url):
    """Espera o servidor subir por 2 segundos e abre a aba perfeita e limpa no navegador."""
    time.sleep(2)
    webbrowser.open(url)

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
        
        # Dispara a abertura do navegador de forma forçada no IP correto e não no 0.0.0.0
        threading.Thread(target=open_browser_delayed, args=(f"http://localhost:{PORTA}",), daemon=True).start()
    print("="*60 + "\n")
    
    # ATENÇÃO: O Flet >= 0.81.0 precisa usar ft.run(). Usar ft.app causa crashes silenciosos e websocket timeout.
    ft.run(
        target=main, 
        assets_dir=ASSETS_DIR,
        upload_dir=UPLOAD_ABS_PATH,
        port=PORTA,
        host="0.0.0.0",  # Precisa escutar em 0.0.0.0 para o celular conseguir conectar
        view=None        # Bloqueia o navegador de abrir na url 0.0.0.0 (a Thread ali em cima faz esse trabalho por nós)
    )