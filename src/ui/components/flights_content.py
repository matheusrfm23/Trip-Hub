import flet as ft
from src.ui.components.flights.flights_manager import FlightsManager

class FlightsContent(FlightsManager):
    """
    Wrapper para manter compatibilidade com importações antigas.
    A lógica real foi movida para src/ui/components/flights/flights_manager.py
    """
    def __init__(self, page: ft.Page):
        super().__init__(page)