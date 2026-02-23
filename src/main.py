import logging
import os
import flet as ft
# [ATUALIZADO] Importando MEU_IP e PORTA centralizados
from src.core.config import AppConfig, ASSETS_DIR, UPLOAD_ABS_PATH, MEU_IP, PORTA
from src.core.router import Router
from src.logic.auth_service import AuthService
from src.data.database import Database
from src.ui.components.modal_preview import ModalPreview

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] 
)
logger = logging.getLogger("TripHub.Main")

async def main(page: ft.Page):
    logger.info(">>> STARTUP: Iniciando Trip Hub...")

    # --- 1. Verificação de Integridade ---
    try:
        await AuthService.perform_integrity_check()
    except Exception as e:
        logger.error(f"Erro na verificação de integridade: {e}")

    # --- 2. Configuração Visual ---
    page.title = AppConfig.WINDOW_TITLE
    page.window_width = 400
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK
    page.padding = 0
    page.spacing = 0

    # --- 3. Infraestrutura ---
    try:
        db = Database()
        db.initialize()
        logger.info("Banco de dados conectado.")
    except Exception as e:
        logger.critical(f"FALHA NO BANCO DE DADOS: {e}")

    # Modal Global
    modal_preview = ModalPreview(page)
    modal_preview.register()
    page.modal_preview = modal_preview 

    # --- 4. Roteamento ---
    router = Router(page)
    
    def window_event(e):
        if e.data == "resize": page.update()
    page.on_window_event = window_event

    # --- 5. INICIALIZAÇÃO FORÇADA ---
    initial_route = page.route if page.route and page.route != "/" else "/login"
    logger.info(f"Definindo rota inicial para: {initial_route}")
    
    # Previne tela branca inicial chamando o router manualmente
    await router.route_change(initial_route) 
    page.go(initial_route)

if __name__ == "__main__":
    
    print("\n" + "="*60)
    print(f"🚀 TRIP HUB SERVER (Docker/Dev Mode)")
    print(f"📡 ACESSO LOCAL (Neste PC):   http://localhost:{PORTA}")
    
    # Lógica inteligente para Docker:
    # Se o IP detectado for interno do Docker (começa com 172 ou 10), avisa o usuário
    # para usar o IP real da máquina (Host).
    if MEU_IP.startswith("172.") or MEU_IP.startswith("10."):
        print(f"📱 ACESSO EXTERNO (WIFI):   O app está rodando isolado no Docker.")
        print(f"                           Descubra o IP do seu PC na rede (ipconfig/ifconfig)")
        print(f"                           e acesse http://<IP-DO-PC>:{PORTA}")
    else:
        print(f"📱 ACESSO EXTERNO (WIFI):   http://{MEU_IP}:{PORTA}")
        
    print("="*60 + "\n")
    
    # [IMPORTANTE] host='0.0.0.0' é o que libera o acesso externo/docker
    ft.app(
        target=main, 
        assets_dir=ASSETS_DIR,
        upload_dir=UPLOAD_ABS_PATH,
        port=PORTA,
        view=ft.AppView.WEB_BROWSER,
        host='0.0.0.0' 
    )