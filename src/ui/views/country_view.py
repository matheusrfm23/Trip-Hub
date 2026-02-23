# ARQUIVO: src/ui/views/country_view.py
import flet as ft
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
            bgcolor=self.cfg["color"],
            content=ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=lambda _: self.main_page.go("/dashboard")),
                ft.Container(content=self.country_row, expand=True, clip_behavior=ft.ClipBehavior.HARD_EDGE)
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # --- SELETOR DE CATEGORIA ---
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
        
        # --- FAB (Floating Action Button) ---
        # [RESTAURADO E POLIDO]
        self.floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.CYAN,
            on_click=self._on_fab_click
        )

        # Carrega o conteúdo inicial
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
        self.top_bar.bgcolor = self.cfg["color"]
        self._build_country_selector()
        self.top_bar.update()
        self._load_content(True)

    def _set_category(self, key):
        self.current_category = key
        self._build_cat_selector()
        self.cat_row.update()
        self._load_content(True)

    def _load_content(self, should_update=True):
        try:
            # Obtém o conteúdo da Factory
            # Nota: O conteúdo retornado pode ser um PlaceTab ou um CalculatorWrapper
            new_content = ContentFactory.get_content(self.main_page, self.current_country, self.current_category)
            self.content_area.content = new_content

            # [LÓGICA FAB] Mostra o FAB apenas se o conteúdo suportar adição (tiver o método open_add_dialog)
            has_add_feature = hasattr(new_content, "open_add_dialog")

            # Atualiza a visibilidade do FAB
            if self.floating_action_button:
                self.floating_action_button.visible = has_add_feature

            if should_update:
                self.content_area.update()
                # Atualiza o FAB na view (precisa chamar update da view ou do FAB se já montado)
                if self.page: self.update()
        except Exception as e:
            print(f"Erro ao carregar factory: {e}")
            self.content_area.content = ft.Text(f"Erro: {e}", color="red")
            if should_update: self.content_area.update()

    def _on_fab_click(self, e):
        # Redireciona o clique para o componente filho (PlaceTab)
        current_content = self.content_area.content
        if hasattr(current_content, "open_add_dialog"):
            current_content.open_add_dialog(e)
        else:
            print("Conteúdo atual não suporta adição.")