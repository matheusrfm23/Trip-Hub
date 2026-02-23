import flet as ft

class LogisticsContent(ft.Column):
    def __init__(self):
        super().__init__()
        self.controls = [
            ft.Text("Logística & Utilidades", size=22, weight="bold"),
            ft.Text("Ferramentas úteis para a rua.", color=ft.Colors.GREY),
            ft.Divider(),
            self._build_utility_tile("Onde estou?", "Rua atual via GPS", ft.Icons.MY_LOCATION),
            self._build_utility_tile("Calculadora de Uber", "Estimativa de custo", ft.Icons.LOCAL_TAXI),
            self._build_utility_tile("Tradutor Rápido", "Português <-> Espanhol", ft.Icons.TRANSLATE),
        ]

    def _build_utility_tile(self, title, subtitle, icon):
        return ft.ListTile(
            leading=ft.Icon(icon, color=ft.Colors.CYAN),
            title=ft.Text(title, color=ft.Colors.WHITE),
            subtitle=ft.Text(subtitle, color=ft.Colors.GREY_500),
            bgcolor=ft.Colors.GREY_900,
        )