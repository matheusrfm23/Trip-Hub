import flet as ft
# Observe como importamos do novo local consolidado
from src.ui.components.places.place_tab import PlaceTab

class ContentFactory:
    """
    Responsável por fabricar o conteúdo correto para cada aba de país.
    Isola a CountryView da implementação real das abas.
    """
    
    @staticmethod
    def get_content(page: ft.Page, country_code: str, category: str):
        """
        Retorna o Widget apropriado baseando-se no país e categoria.
        
        :param page: Referência à página principal
        :param country_code: 'br', 'ar', 'py'
        :param category: 'hotel', 'food', 'tour', 'shop'
        """
        
        # --- FUTURO: HOOKS DE CUSTOMIZAÇÃO ---
        # Aqui é onde você inserirá a lógica do Paraguai futuramente.
        # Exemplo hipotético:
        # if country_code == 'py' and category == 'shop':
        #     return ParaguayShoppingTab(page)
        
        # --- COMPORTAMENTO PADRÃO ---
        # Para todos os casos onde não há customização, usamos o PlaceTab genérico.
        # Mapeamento de categorias de string simples para chaves internas se necessário,
        # mas atualmente o sistema usa 'hotel', 'food', 'tour', 'shop' diretamente.
        
        return PlaceTab(page, country_code, category)