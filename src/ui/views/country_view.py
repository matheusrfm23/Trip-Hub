# ARQUIVO: src/ui/views/country_view.py
# CHANGE LOG:
# - Correção do FAB (Botão flutuante) que mostrava o ícone "+" duplicado (removida a propriedade 'icon', mantendo apenas 'content').

import flet as ft
from src.ui.components.content_factory import ContentFactory

class CountryView(ft.View):
    def __init__(self, page: ft.Page, country_code: str):
        super().__init__(
            route=f"/country/{country_code}",
            padding=0,
            bgcolor=ft.Colors.BLACK,
            appbar=ft.AppBar(
                title=ft.Text("TripHub", weight="bold", font_family="Verdana"),
                center_title=True,
                bgcolor=ft.Colors.BLACK,
                leading=ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    tooltip="Voltar",
                    icon_color=ft.Colors.WHITE,
                    on_click=lambda _: page.run_task(self._go_home)
                )
            ),
            floating_action_button=ft.FloatingActionButton(
                bgcolor=ft.Colors.CYAN,
                content=ft.Icon(ft.Icons.ADD, color=ft.Colors.BLACK, weight=900), # <- Apenas content, sem 'icon=ft.Icons.ADD'
                on_click=self._on_fab_click,
                visible=False,
                shape=ft.CircleBorder()
            )
        )
        self.main_page = page
        self.current_country = country_code
        self.current_category = "hotel"
        
        self.configs = {
            "br": {"name": "Brasil", "flag": "🇧🇷", "color": ft.Colors.GREEN_900},
            "ar": {"name": "Argentina", "flag": "🇦🇷", "color": ft.Colors.BLUE_900},
            "py": {"name": "Paraguai", "flag": "🇵🇾", "color": ft.Colors.RED_900},
        }
        self.cfg = self.configs.get(country_code, self.configs["br"])

        # --- SELETOR DE PAÍS ---
        self.country_row = ft.Row(scroll=ft.ScrollMode.HIDDEN, spacing=8)
        self._build_country_selector()

        # --- HEADER DE CONTEXTO ---
        self.header_title = ft.Text(self.cfg["name"].upper(), size=20, weight="bold", color=self.cfg["color"])
        self.header = ft.Container(
            padding=ft.padding.only(left=15, right=15, top=10, bottom=5),
            content=ft.Column([
                self.header_title,
                self.country_row
            ], spacing=10)
        )

        # --- SELETOR DE CATEGORIA (Moderno) ---
        self.cat_row = ft.Row(scroll=ft.ScrollMode.HIDDEN, expand=True, spacing=15)
        self.categories = [
            ("hotel", "Hospedagem", ft.Icons.BED),
            ("food", "Gastronomia", ft.Icons.RESTAURANT),
            ("tour", "Passeios", ft.Icons.MAP),
            ("shop", "Compras", ft.Icons.SHOPPING_BAG)
        ]
        self._build_cat_selector()

        self.cat_container = ft.Container(
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=ft.Colors.BLACK,
            content=self.cat_row
        )

        # --- ÁREA DE CONTEÚDO ---
        self.content_area = ft.Container(
            expand=True,
            bgcolor=ft.Colors.BLACK,
            alignment=ft.Alignment(0, -1) 
        )
        
        self._load_content(should_update=False)

        self.controls = [
            self.header,
            self.cat_container,
            ft.Divider(height=1, color=ft.Colors.WHITE10),
            self.content_area
        ]

    async def _go_home(self):
        await self.main_page.push_route("/dashboard")

    def _build_country_selector(self):
        self.country_row.controls = []
        for code, data in self.configs.items():
            is_selected = (code == self.current_country)
            
            btn = ft.Container(
                bgcolor=ft.Colors.WHITE24 if is_selected else ft.Colors.BLACK26,
                border_radius=20,
                border=ft.border.all(1, ft.Colors.WHITE if is_selected else ft.Colors.TRANSPARENT),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=lambda e, c=code: self._set_country(c),
                content=ft.Row([
                    ft.Text(data["flag"], size=16),
                    ft.Text(data["name"], size=12, weight="bold" if is_selected else "normal",
                           color=ft.Colors.WHITE if is_selected else ft.Colors.WHITE54)
                ], spacing=6, alignment="center"),
                ink=True
            )
            self.country_row.controls.append(btn)

    def _build_cat_selector(self):
        self.cat_row.controls = []
        for key, label, icon in self.categories:
            is_selected = (key == self.current_category)
            color = ft.Colors.CYAN if is_selected else ft.Colors.GREY_700
            text_color = ft.Colors.WHITE if is_selected else ft.Colors.GREY

            btn = ft.Column([
                ft.Container(
                    padding=12,
                    border_radius=12,
                    bgcolor=ft.Colors.CYAN_900 if is_selected else ft.Colors.GREY_900,
                    content=ft.Icon(icon, size=24, color=ft.Colors.WHITE if is_selected else ft.Colors.GREY),
                    on_click=lambda e, k=key: self._set_category(k),
                    ink=True
                ),
                ft.Text(label, size=10, color=text_color, weight="bold" if is_selected else "normal")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
            
            self.cat_row.controls.append(btn)

    def _set_country(self, code):
        self.current_country = code
        self.cfg = self.configs.get(code, self.configs["br"])

        self.header_title.value = self.cfg["name"].upper()
        self.header_title.color = self.cfg["color"]
        
        self._build_country_selector()
        self.header.update()
        self._load_content(True)

    def _set_category(self, key):
        self.current_category = key
        self._build_cat_selector()
        self.cat_row.update()
        self._load_content(True)

    def _load_content(self, should_update=True):
        try:
            new_content = ContentFactory.get_content(self.main_page, self.current_country, self.current_category)
            self.content_area.content = new_content

            target_control = new_content
            if isinstance(new_content, ft.Container) and new_content.content:
                target_control = new_content.content

            has_add_feature = False
            if hasattr(target_control, "open_add_dialog") and getattr(target_control, "is_admin", False):
                has_add_feature = True
            elif hasattr(new_content, "open_add_dialog") and getattr(new_content, "is_admin", False):
                has_add_feature = True

            if self.floating_action_button:
                self.floating_action_button.visible = has_add_feature

            if should_update:
                self.content_area.update()
                if self.page: self.update()

        except Exception as e:
            print(f"Erro ao carregar factory: {e}")
            self.content_area.content = ft.Container(
                alignment=ft.Alignment(0, 0),
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED, size=50),
                    ft.Text(f"Erro ao carregar módulo.\n{e}", color=ft.Colors.RED, text_align="center")
                ], horizontal_alignment="center")
            )
            if should_update: self.content_area.update()

    def _on_fab_click(self, e):
        current_content = self.content_area.content
        if not current_content: return

        if hasattr(current_content, "open_add_dialog"):
            current_content.open_add_dialog(e)
        elif isinstance(current_content, ft.Container) and hasattr(current_content.content, "open_add_dialog"):
            current_content.content.open_add_dialog(e)
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Não é possível adicionar itens aqui."), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()