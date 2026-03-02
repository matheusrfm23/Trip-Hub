import flet as ft
import traceback
from src.logic.place_service import PlaceService
from src.ui.components.places.cards.modern_hotel_card import ModernHotelCard 
from src.ui.components.places.cards.compact_card import CompactCard
from src.ui.components.places.place_form import PlaceForm
from src.ui.components.places.place_modal_manager import PlaceModalManager

class PlaceTab(ft.Column):
    def __init__(self, page: ft.Page, country_code: str, category: str):
        super().__init__(expand=True)
        self.main_page = page
        self.country_code = country_code
        self.category = category
        self.places = []
        
        user = getattr(page, 'user_profile', {})
        self.current_user_id = user.get("name", "User1")
        self.is_admin = user.get("role") == "ADMIN"
        self.is_hotel = (category == "hotel")
        
        self.modal_manager = PlaceModalManager(page, on_data_change=self.load_data)
        
        self.content_view = ft.ListView(expand=True, spacing=20, padding=10) if self.is_hotel else \
                            ft.GridView(expand=True, runs_count=2, child_aspect_ratio=0.8, spacing=15, run_spacing=15, padding=15)
        
        # [PROTECÃO] Inicia VISÍVEL. Se iniciar invisível e tentar dar update cedo demais, quebra.
        self.loading = ft.ProgressBar(width=100, color=ft.Colors.CYAN, visible=True)
        
        self.place_form = PlaceForm(self.main_page, on_save_callback=self._on_form_save)
        
        if self.is_admin:
            # Tenta definir o FAB, mas ignora erro se a página ainda não estiver pronta
            try:
                self.main_page.floating_action_button = ft.FloatingActionButton(
                    icon=ft.Icons.ADD, bgcolor=ft.Colors.CYAN, 
                    on_click=lambda _: self.place_form.open(self.category, item=None)
                )
                self.main_page.update()
            except: pass

        self.controls = [
            ft.Container(self.loading, alignment=ft.Alignment(0,0), height=5),
            self.content_view
        ]

    def did_mount(self):
        # [CRÍTICO] Não chame self.update() aqui. Apenas inicie a busca de dados.
        self.main_page.run_task(self._fetch_data)

    def load_data(self):
        self.loading.visible = True
        try: self.update()
        except: pass
        self.main_page.run_task(self._fetch_data)

    async def _fetch_data(self):
        try:
            self.places = await PlaceService.get_places(self.country_code, self.category)
            items_controls = []
            
            if not self.places:
                items_controls.append(ft.Container(content=ft.Text("Vazio.", color=ft.Colors.GREY_600), alignment=ft.Alignment(0,0), padding=50))
            else:
                for item in self.places:
                    images = self.modal_manager._get_images(item["id"])
                    
                    if self.is_hotel:
                        # [CORREÇÃO] Ajuste nas chamadas de callback para usar run_task e nomes corretos
                        callbacks = {
                            "on_edit": lambda i: self._open_edit_logic(i),
                            "on_delete": lambda i: self._delete_direct(i),
                            "on_add_photo": lambda pid: self.modal_manager.open_photo_manager(pid),
                            "on_delete_photo": lambda path: self.main_page.run_task(self.modal_manager.delete_photo, path),
                            
                            # CORRIGIDO: Usa safe_launch_url (o nome correto) via run_task
                            "on_open_map": lambda link: self.main_page.run_task(self.modal_manager.safe_launch_url, link),
                            
                            # CORRIGIDO: Usa smart_copy via run_task (removemos o inexistente _run_async)
                            "on_copy": lambda txt: self.main_page.run_task(self.modal_manager.smart_copy, txt),
                            
                            "on_zoom": self.modal_manager.open_zoom
                        }
                        items_controls.append(ModernHotelCard(item, self.is_admin, images, callbacks))
                    else:
                        items_controls.append(CompactCard(
                            item=item, 
                            current_user=self.current_user_id, 
                            images=images, 
                            on_click_callback=lambda i: self.modal_manager.show_details(i, self._open_edit_logic, self._delete_direct),
                            on_vote_callback=self._handle_vote_click
                        ))
            self.content_view.controls = items_controls
        except Exception as e:
            traceback.print_exc()
        finally:
            self.loading.visible = False
            # Update seguro
            try: self.update()
            except: pass

    def _open_edit_logic(self, item):
        if self.modal_manager.current_modal and self.modal_manager.current_modal.open:
            self.modal_manager.close_modal(self.modal_manager.current_modal)
        self.place_form.open(self.category, item=item)

    async def _on_form_save(self, item_id, data_dict):
        self.loading.visible = True; self.update()
        data_dict.update({"country": self.country_code, "category": self.category})
        if item_id: await PlaceService.update_place(item_id, data_dict)
        else: await PlaceService.add_place(data_dict)
        self.load_data()

    def _delete_direct(self, item): self.main_page.run_task(self._delete_async, item)
    async def _delete_async(self, item):
        await PlaceService.delete_place(item["id"], self.country_code, self.category)
        if self.modal_manager.current_modal: self.modal_manager.close_modal(self.modal_manager.current_modal)
        self.load_data()

    def _handle_vote_click(self, e, item):
        e.control.icon = ft.Icons.FAVORITE; e.control.icon_color = ft.Colors.RED; e.control.update() 
        self.main_page.run_task(self._toggle_vote_async, item)

    async def _toggle_vote_async(self, item):
        await PlaceService.toggle_vote(item["id"], self.country_code, self.category, self.current_user_id)
        await self._fetch_data()