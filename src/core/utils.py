import os
import datetime
import mimetypes
import aiohttp
import asyncio
import flet as ft
from src.core.config import UPLOAD_ABS_PATH, UPLOAD_REL_PATH, MEU_IP, PORTA

# --- CONFIGURAÇÕES GERAIS ---

# Constrói a URL baseada nas configurações centrais
HOST_URL = f"http://{MEU_IP}:{PORTA}"

# Sua API Key da OpenRouteService
ORS_API_KEY = "5b3ce3597851110001cf6248a061c6cafbb549929ce06e637c9660ac"


# --- FUNÇÕES DE UTILIDADE ---

def format_size(size):
    for u in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.1f} {u}"
        size /= 1024
    return f"{size:.1f} TB"

def get_file_details(filename):
    """
    Retorna metadados do arquivo para a UI.
    """
    try:
        path = os.path.join(UPLOAD_ABS_PATH, filename)
        if not os.path.exists(path): return None
        
        stats = os.stat(path)
        size_str = format_size(stats.st_size)
        date_str = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m %H:%M')
        
        mime, _ = mimetypes.guess_type(filename)
        is_img = mime and mime.startswith("image")
        
        # Construção da URL relativa e absoluta
        url = f"/{UPLOAD_REL_PATH}/{filename}"
        full_url = f"{HOST_URL}{url}" 
        
        icon, color = ft.Icons.INSERT_DRIVE_FILE, ft.Colors.GREY_400
        if is_img: 
            icon, color = ft.Icons.IMAGE, ft.Colors.BLUE
        elif mime and mime.startswith("video"): 
            icon, color = ft.Icons.VIDEO_FILE, ft.Colors.BLUE_400
        elif filename is not None and filename.endswith(".pdf"): 
            icon, color = ft.Icons.PICTURE_AS_PDF, ft.Colors.RED_400
        
        return {
            "name": filename, 
            "is_img": is_img, 
            "url": url, 
            "full_url": full_url, 
            "icon": icon, 
            "color": color, 
            "size": size_str, 
            "date": date_str
        }
    except Exception as e:
        print(f"Erro ao ler detalhes do arquivo: {e}")
        return None

async def get_address_from_gps(lat, lon):
    """
    Converte Latitude e Longitude em um endereço legível usando OpenRouteService.
    """
    url = "https://api.openrouteservice.org/geocode/reverse"
    params = {
        "api_key": ORS_API_KEY,
        "point.lat": lat,
        "point.lon": lon,
        "size": 1  # Apenas o resultado mais preciso
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["features"]:
                        props = data["features"][0]["properties"]
                        # Tenta montar um endereço amigável
                        street = props.get("street", "")
                        name = props.get("name", "")
                        locality = props.get("locality", "")
                        
                        # Prioriza o nome do local (ex: "Shopping China") ou a rua
                        final_name = name if name else street
                        
                        if final_name and locality:
                            return f"{final_name}, {locality}"
                        elif final_name:
                            return final_name
                        elif locality:
                            return f"Em {locality}"
                        else:
                            return "Localização não identificada"
    except Exception as e:
        print(f"Erro no GPS API: {e}")
    
    return None