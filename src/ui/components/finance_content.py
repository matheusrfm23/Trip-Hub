import flet as ft
from src.ui.components.finance.finance_manager import FinanceManager

class FinanceContent(FinanceManager):
    """
    Classe Wrapper para manter compatibilidade com o código legado.
    Herda diretamente do novo FinanceManager.
    """
    def __init__(self, page: ft.Page):
        super().__init__(page)