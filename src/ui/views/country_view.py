import flet as ft
import traceback
from src.logic.place_service import PlaceService
from src.ui.components.places.place_modal_manager import PlaceModalManager
from src.ui.components.places.place_form import PlaceForm
from src.ui.components.places.cards.modern_hotel_card import ModernHotelCard
from src.ui.components.places.cards.compact_card import CompactCard

class CountryView(ft.View):
    def __init__(self, page: ft.Page, country_code: str):
        self.main_page = page
        self.country_code = country_code
        self.current_category = "hotel"
        
        # Configurações do País
        self.configs = {
            "br": {"name": "Brasil", "flag": "🇧🇷", "color": ft.Colors.GREEN_900, "grad": [ft.Colors.GREEN_900, ft.Colors.BLACK]},
            "ar": {"name": "Argentina", "flag": "🇦🇷", "color": ft.Colors.BLUE_900, "grad": [ft.Colors.BLUE_900, ft.Colors.BLACK]},
            "py": {"name": "Paraguai", "flag": "🇵🇾", "color": ft.Colors.RED_900, "grad": [ft.Colors.RED_900, ft.Colors.BLACK]},
        }
        self.cfg = self.configs.get(country_code, self.configs["br"])

        # Gerenciadores de Lógica (Modais e Formulários)
        self.modal_manager = PlaceModalManager(page, on_data_change=self._refresh_data)
        self.place_form = PlaceForm(page, on_save_callback=self._on_form_save)

        # Botão de Adicionar (FAB) - Exigência do cliente
        fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.CYAN,
            on_click=lambda _: self.place_form.open(self.current_category, None)
        )

        super().__init__(
            route=f"/country/{country_code}",
            padding=0,
            bgcolor=ft.Colors.BLACK,
            floating_action_button=fab
        )

        # Estado
        user = getattr(page, 'user_profile', {})
        self.current_user_id = user.get("name", "User1")
        self.is_admin = user.get("role") == "ADMIN"
        
        # Componentes de UI
        self.content_area = ft.Container(expand=True, padding=10, alignment=ft.Alignment(0, -1))
        self.loading = ft.ProgressBar(width=100, color=ft.Colors.CYAN, visible=False)

        # Montagem do Layout Principal
        self.controls = [
            self._build_header(),
            self._build_category_selector(),
            ft.Container(content=self.loading, alignment=ft.Alignment(0, 0), height=5), # Barra de loading discreta
            self.content_area
        ]

    def did_mount(self):
        # Inicia carregamento de dados assim que a view é montada
        self.page.run_task(self._load_data)

    def _refresh_data(self):
        self.loading.visible = True
        self.update()
        self.page.run_task(self._load_data)

    async def _load_data(self):
        self.loading.visible = True
        try:
            self.update()
        except: pass

        try:
            places = await PlaceService.get_places(self.country_code, self.current_category)
            self._render_items(places)
        except Exception as e:
            print(f"Erro ao carregar locais: {e}")
            traceback.print_exc()
            self.content_area.content = ft.Container(
                content=ft.Text(f"Erro ao carregar: {e}", color=ft.Colors.RED),
                alignment=ft.Alignment(0, 0),
                padding=20
            )
            self.content_area.update()
        finally:
            self.loading.visible = False
            try: self.update()
            except: pass

    def _render_items(self, places):
        if not places:
            self.content_area.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SEARCH_OFF, size=50, color=ft.Colors.GREY_700),
                    ft.Text("Nenhum local encontrado.", color=ft.Colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                padding=50
            )
            self.content_area.update()
            return

        is_hotel = (self.current_category == "hotel")

        # Grid para categorias comuns, Lista para Hoteis (cards grandes)
        if not is_hotel:
            grid = ft.GridView(expand=True, runs_count=2, child_aspect_ratio=0.85, spacing=10, run_spacing=10)
            for item in places:
                card = CompactCard(
                    item=item,
                    current_user=self.current_user_id,
                    images=self.modal_manager._get_images(item["id"]),
                    on_click_callback=lambda i: self.modal_manager.show_details(i, self._open_edit, self._delete_place),
                    on_vote_callback=self._handle_vote
                )
                grid.controls.append(card)
            self.content_area.content = grid
        else:
            # Lista Vertical para Hoteis
            col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)
            for item in places:
                # Callbacks específicos para o ModernHotelCard
                callbacks = {
                    "on_edit": self._open_edit,
                    "on_delete": self._delete_place,
                    "on_add_photo": self.modal_manager.open_photo_manager,
                    "on_delete_photo": self.modal_manager.delete_photo,
                    "on_open_map": lambda link: self.page.run_task(self.modal_manager.safe_launch_url, link),
                    "on_copy": lambda txt: self.page.run_task(self.modal_manager.smart_copy, txt),
                    "on_zoom": self.modal_manager.open_zoom
                }
                card = ModernHotelCard(
                    item=item,
                    is_admin=self.is_admin,
                    images=self.modal_manager._get_images(item["id"]),
                    callbacks=callbacks
                )
                col.controls.append(card)
            self.content_area.content = col

        self.content_area.update()

    # --- ACTIONS ---

    def _open_edit(self, item):
        if self.modal_manager.current_modal and self.modal_manager.current_modal.open:
            self.modal_manager.close_modal(self.modal_manager.current_modal)
        self.place_form.open(self.current_category, item)

    def _delete_place(self, item):
        # Wrapper para deletar item
        async def _action():
            await PlaceService.delete_place(item["id"], self.country_code, self.current_category)
            if self.modal_manager.current_modal:
                self.modal_manager.close_modal(self.modal_manager.current_modal)
            self._refresh_data()
            
        self.page.run_task(_action)

    def _handle_vote(self, e, item):
        # Ação de votar
        async def _action():
            await PlaceService.toggle_vote(item["id"], self.country_code, self.current_category, self.current_user_id)
            # Atualiza dados silenciosamente para refletir votos novos
            places = await PlaceService.get_places(self.country_code, self.current_category)
            # Não rebuilda tudo para não perder scroll, idealmente atualizaria só o card,
            # mas por simplicidade e garantia de consistência, recarregamos.
            # Se quiser otimizar, poderia atualizar só o contador localmente.
            self._render_items(places)
            self.update()

        self.page.run_task(_action)

    async def _on_form_save(self, item_id, data_dict):
        self.loading.visible = True
        self.update()

        data_dict.update({"country": self.country_code, "category": self.current_category})

        if item_id:
            await PlaceService.update_place(item_id, data_dict)
        else:
            data_dict["added_by"] = self.current_user_id
            await PlaceService.add_place(data_dict)

        self._refresh_data()

    # --- UI BUILDERS ---

    def _build_header(self):
        return ft.Container(
            height=80,
            decoration=ft.BoxDecoration(
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1),
                    end=ft.Alignment(0, 1),
                    colors=self.cfg.get("grad", [ft.Colors.GREY_900, ft.Colors.BLACK])
                )
            ),
            padding=ft.padding.symmetric(horizontal=15),
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    on_click=lambda _: self._navigate_home()
                ),
                ft.Column([
                    ft.Text(self.cfg["name"].upper(), size=12, weight="bold", color=ft.Colors.WHITE54),
                    ft.Row([
                        ft.Text(self.cfg["flag"], size=24),
                        ft.Text(self.cfg["name"], size=20, weight="bold", color=ft.Colors.WHITE)
                    ], spacing=10)
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(expand=True),
                # Seletor de País Rápido (Chips)
                self._build_mini_country_selector()
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _navigate_home(self):
        # Hack para garantir que o histórico funcione bem
        # self.page.views.clear() # Não limpar para manter histórico se desejado, mas aqui limpamos para evitar acúmulo
        self.page.go("/dashboard")

    def _build_mini_country_selector(self):
        row = ft.Row(spacing=5)
        for code, data in self.configs.items():
            if code == self.country_code: continue # Não mostra o atual
            row.controls.append(
                ft.Container(
                    content=ft.Text(data["flag"], size=18),
                    padding=8,
                    bgcolor=ft.Colors.BLACK26,
                    border_radius=20,
                    ink=True,
                    on_click=lambda e, c=code: self.page.go(f"/country/{c}")
                )
            )
        return row

    def _build_category_selector(self):
        cats = [
            ("hotel", "Hospedagem", ft.Icons.BED),
            ("food", "Comer", ft.Icons.RESTAURANT),
            ("tour", "Passeios", ft.Icons.MAP),
            ("shop", "Compras", ft.Icons.SHOPPING_BAG)
        ]

        row = ft.Row(scroll=ft.ScrollMode.HIDDEN, spacing=10)

        for key, label, icon in cats:
            is_selected = (key == self.current_category)
            color = ft.Colors.CYAN if is_selected else ft.Colors.GREY_600
            bg = ft.Colors.with_opacity(0.1, ft.Colors.CYAN) if is_selected else ft.Colors.TRANSPARENT
            
            btn = ft.Container(
                bgcolor=bg,
                border_radius=12,
                border=ft.border.all(1, color if is_selected else ft.Colors.TRANSPARENT),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=lambda e, k=key: self._set_category(k),
                content=ft.Row([
                    ft.Icon(icon, size=16, color=color),
                    ft.Text(label, color=color, size=13, weight="bold" if is_selected else "normal")
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER)
            )
            row.controls.append(btn)

        return ft.Container(
            padding=ft.padding.only(left=15, right=15, bottom=10),
            content=row
        )

    def _set_category(self, key):
        if self.current_category == key: return
        self.current_category = key
        # Reconstrói seletor para atualizar visual (poderia otimizar, mas é rápido)
        self.controls[1] = self._build_category_selector()
        self.update()
        self._refresh_data()
