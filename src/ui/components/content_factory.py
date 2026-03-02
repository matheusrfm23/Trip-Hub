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
        
        return PlaceTab(page, country_code, category)