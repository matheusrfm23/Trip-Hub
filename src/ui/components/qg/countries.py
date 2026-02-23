import flet as ft

class QGCountries(ft.Row):
    def __init__(self, navigate_callback):
        super().__init__(spacing=10, scroll=ft.ScrollMode.HIDDEN)
        self.navigate_callback = navigate_callback
        
        self.controls = [
            self._build_country_btn("Brasil", "br", "🇧🇷", ft.Colors.GREEN_900),
            self._build_country_btn("Argentina", "ar", "🇦🇷", ft.Colors.BLUE_900),
            self._build_country_btn("Paraguai", "py", "🇵🇾", ft.Colors.RED_900),
        ]

    def _build_country_btn(self, name, code, flag, color):
        return ft.Container(
            width=110, height=80, 
            bgcolor=color, 
            border_radius=12, 
            padding=10, 
            ink=True, 
            on_click=lambda e: self.navigate_callback(name, code, color), 
            content=ft.Column([
                ft.Text(flag, size=20), 
                ft.Container(expand=True), 
                ft.Text(name, weight="bold", size=14)
            ])
        )