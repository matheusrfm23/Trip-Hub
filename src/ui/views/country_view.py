import flet as ft
# Removemos a importação direta de PlaceTab
# from src.ui.components.place_tab import PlaceTab
# Importamos a Factory (O Cérebro)
from src.ui.components.content_factory import ContentFactory

class CountryView(ft.View):
    def __init__(self, page: ft.Page, country_code: str):
        super().__init__(route=f"/country/{country_code}", padding=0, bgcolor=ft.Colors.BLACK)
        self.main_page = page
        self.current_country = country_code
        self.current_category = "hotel"
        
        self.configs = {
            "br": {"name": "Brasil", "flag": "🇧🇷", "color": ft.Colors.GREEN_900},
            "ar": {"name": "Argentina", "flag": "🇦🇷", "color": ft.Colors.BLUE_900},
            "py": {"name": "Paraguai", "flag": "🇵🇾", "color": ft.Colors.RED_900},
        }
        self.cfg = self.configs.get(country_code, self.configs["br"])

        # --- SELETOR DE PAÍS (Chip Style) ---
        self.country_row = ft.Row(scroll=ft.ScrollMode.HIDDEN, spacing=10)
        self._build_country_selector()

        # --- TOP BAR ---
        self.top_bar = ft.Container(
            padding=ft.padding.only(left=5, right=10, top=5, bottom=5),
            bgcolor=self.cfg["color"], # Usa a cor do país
            content=ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda _: self.main_page.go("/dashboard")),
                ft.Container(content=self.country_row, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # --- SELETOR DE CATEGORIA (Manual Tabs) ---
        self.cat_row = ft.Row(scroll=ft.ScrollMode.HIDDEN, expand=True, spacing=5)
        self.categories = [
            ("hotel", "Hospedagem", ft.Icons.BED),
            ("food", "Comer", ft.Icons.RESTAURANT),
            ("tour", "Passeios", ft.Icons.MAP),
            ("shop", "Compras", ft.Icons.SHOPPING_BAG)
        ]
        self._build_cat_selector()

        self.cat_container = ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=0),
            bgcolor=ft.Colors.BLACK,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.WHITE10)),
            content=self.cat_row
        )

        # --- ÁREA DE CONTEÚDO ---
        self.content_area = ft.Container(expand=True, bgcolor=ft.Colors.BLACK)
        
        # Carrega o conteúdo inicial usando a Factory
        self._load_content(should_update=False)

        self.controls = [
            self.top_bar,
            self.cat_container,
            self.content_area
        ]

    def _build_country_selector(self):
        self.country_row.controls = []
        for code, data in self.configs.items():
            is_selected = (code == self.current_country)
            
            btn = ft.Container(
                bgcolor=ft.Colors.BLACK26 if is_selected else ft.Colors.TRANSPARENT,
                border_radius=20,
                border=ft.border.all(1, ft.Colors.WHITE if is_selected else ft.Colors.TRANSPARENT),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                on_click=lambda e, c=code: self._set_country(c),
                content=ft.Row([
                    ft.Text(data["flag"], size=16),
                    ft.Text(data["name"], size=12, weight="bold" if is_selected else "normal", color=ft.Colors.WHITE if is_selected else ft.Colors.WHITE54)
                ], spacing=5, alignment="center")
            )
            self.country_row.controls.append(btn)

    def _build_cat_selector(self):
        self.cat_row.controls = []
        for key, label, icon in self.categories:
            is_selected = (key == self.current_category)
            color = ft.Colors.CYAN if is_selected else ft.Colors.GREY
            
            btn = ft.Container(
                padding=ft.padding.symmetric(vertical=12, horizontal=12),
                border=ft.border.only(bottom=ft.BorderSide(3, color if is_selected else ft.Colors.TRANSPARENT)),
                on_click=lambda e, k=key: self._set_category(k),
                content=ft.Row([
                    ft.Icon(icon, size=18, color=color),
                    ft.Text(label, color=color, size=12, weight="bold" if is_selected else "normal")
                ], spacing=5, alignment="center")
            )
            self.cat_row.controls.append(btn)

    def _set_country(self, code):
        self.current_country = code
        self.cfg = self.configs.get(code, self.configs["br"])
        # Atualiza cor da TopBar
        self.top_bar.bgcolor = self.cfg["color"]
        self._build_country_selector()
        self.top_bar.update() # Atualiza topbar e row
        self._load_content(True)

    def _set_category(self, key):
        self.current_category = key
        self._build_cat_selector()
        self.cat_row.update()
        self._load_content(True)

    def _load_content(self, should_update=True):
        try:
            # === AQUI ESTÁ A INTEGRAÇÃO DA FASE 3 ===
            # Em vez de chamar PlaceTab direto, chamamos a Factory.
            # Se for 'py' e 'shop' no futuro, a Factory entregará a calculadora.
            new_content = ContentFactory.get_content(self.main_page, self.current_country, self.current_category)
            
            self.content_area.content = new_content
            if should_update:
                self.content_area.update()
        except Exception as e:
            print(f"Erro ao carregar factory: {e}")
            self.content_area.content = ft.Text(f"Erro: {e}", color="red")
            if should_update: self.content_area.update()