import os
import secrets
import socket
import flet as ft

# ==============================================================================
# 1. CONFIGURAÇÕES GERAIS DO TRIP HUB
# ==============================================================================
class AppConfig:
    """Configurações visuais e globais da aplicação"""
    WINDOW_TITLE = "Trip Hub"
    WINDOW_WIDTH = 400  
    WINDOW_HEIGHT = 800 
    WINDOW_RESIZABLE = True
    THEME_MODE = ft.ThemeMode.DARK

# ==============================================================================
# 2. INFRAESTRUTURA DE REDE (AUTO-DETECÇÃO DE IP)
# ==============================================================================
def get_lan_ip():
    """
    Descobre o IP da máquina na rede local (ex: 192.168.X.X).
    Essencial para acesso via Celular.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Não envia dados, apenas consulta rota
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Define o IP real da máquina
MEU_IP = get_lan_ip()

# [CORREÇÃO] Porta unificada. Se mudar aqui, muda no servidor inteiro.
PORTA = int(os.getenv("PORT", 8080)) 

# ==============================================================================
# 3. INFRAESTRUTURA DE ARQUIVOS
# ==============================================================================

# Caminhos Absolutos
BASE_DIR = os.getcwd()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(ASSETS_DIR, "data") 

# Caminhos Específicos do Módulo de Upload
UPLOAD_REL_PATH = "uploads"
UPLOAD_ABS_PATH = os.path.join(ASSETS_DIR, UPLOAD_REL_PATH)

# Segurança
if "FLET_SECRET_KEY" not in os.environ:
    os.environ["FLET_SECRET_KEY"] = secrets.token_urlsafe(16)

# ==============================================================================
# 4. GARANTIA DE INTEGRIDADE (SELF-HEALING)
# ==============================================================================
dirs_to_check = [ASSETS_DIR, DATA_DIR, UPLOAD_ABS_PATH]

for directory in dirs_to_check:
    if not os.path.exists(directory):
        print(f" Criando diretório de infraestrutura: {directory}")
        os.makedirs(directory)