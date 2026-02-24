# ARQUIVO: src/main.py
# CHANGE LOG:
# - Atualizada a função de inicialização ft.app() para ft.run() para remover 
#   o DeprecationWarning nas novas versões do Flet, resolvendo conflitos do uvicorn.

import logging
import os
import flet as ft
# [ATUALIZADO] Importando Logger Customizado
from src.core.logger import get_logger
from src.core.config import AppConfig, ASSETS_DIR, UPLOAD_ABS_PATH, MEU_IP, PORTA
from src.core.router import Router
from src.logic.auth_service import AuthService
from src.data.database import Database
from src.ui.components.modal_preview import ModalPreview

# 1. Configuração de Logging (Primeira coisa a rodar)
logger = get_logger("TripHub.Main")

async def main(page: ft.Page):
    logger.info(">>> STARTUP: Iniciando Trip Hub...")

    # --- 2. Inicialização do Banco de Dados (CRÍTICO: Deve ser o primeiro) ---
    try:
        db = Database()
        db.initialize()
        logger.info("Banco de dados conectado e inicializado.")
    except Exception as e:
        logger.critical(f"FALHA CRÍTICA NO BANCO DE DADOS: {e}", exc_info=True)
        # Em caso de falha crítica no DB, a aplicação pode ficar instável

    # --- 3. Verificação de Integridade (Agora seguro pois o DB existe) ---
    try:
        await AuthService.perform_integrity_check()
    except Exception as e:
        logger.error(f"Erro na verificação de integridade: {e}", exc_info=True)

    # --- 4. Configuração Visual ---
    page.title = AppConfig.WINDOW_TITLE
    page.window_width = 400
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK
    page.padding = 0
    page.spacing = 0

    # Modal Global
    modal_preview = ModalPreview(page)
    modal_preview.register()
    page.modal_preview = modal_preview 

    # --- 5. Roteamento ---
    router = Router(page)
    
    def window_event(e):
        if e.data == "resize": page.update()
    page.on_window_event = window_event

    # --- 6. INICIALIZAÇÃO FORÇADA ---
    initial_route = page.route if page.route and page.route != "/" else "/login"
    logger.info(f"Definindo rota inicial para: {initial_route}")
    
    # Previne tela branca inicial chamando o router manualmente
    await router.route_change(initial_route) 
    await page.push_route(initial_route)

if __name__ == "__main__":
    
    print("\n" + "="*60)
    print(f"🚀 TRIP HUB SERVER (Docker/Dev Mode)")
    print(f"📡 ACESSO LOCAL (Neste PC):   http://localhost:{PORTA}")
    
    if MEU_IP.startswith("172.") or MEU_IP.startswith("10."):
        print(f"📱 ACESSO EXTERNO (WIFI):   O app está rodando isolado no Docker.")
        print(f"                           Descubra o IP do seu PC na rede (ipconfig/ifconfig)")
        print(f"                           e acesse http://<IP-DO-PC>:{PORTA}")
    else:
        print(f"📱 ACESSO EXTERNO (WIFI):   http://{MEU_IP}:{PORTA}")
        
    print("="*60 + "\n")
    
    # Substituição correta do ft.app pelo ft.run para Flet 0.81.0+
    # Evita que o FastAPI/Uvicorn se confunda e feche conexões antecipadamente
    run_func = getattr(ft, "run", getattr(ft, "app"))
    
    run_func(
        target=main, 
        assets_dir=ASSETS_DIR,
        upload_dir=UPLOAD_ABS_PATH,
        port=PORTA,
        view=ft.AppView.WEB_BROWSER,
        host='0.0.0.0' 
    )