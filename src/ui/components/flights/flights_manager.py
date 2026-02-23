import flet as ft
import copy
from src.logic.flight_service import FlightService
from src.ui.components.flights.baggage_dialog import BaggageDialogManager
from src.ui.components.flights.qr_dialog import QRDialogManager
from src.ui.components.flights.flight_form import FlightFormManager
from src.ui.components.flights.flight_card import FlightCardManager

class FlightsManager(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page
        self.user = self.main_page.user_profile
        self.flights = []
        
        # Managers
        self.baggage_manager = BaggageDialogManager(self.main_page)
        self.qr_manager = QRDialogManager(self.main_page)
        self.form_manager = FlightFormManager(self.main_page, self.user, self._fetch_data)
        self.card_manager = FlightCardManager(
            self.main_page, 
            self.user, 
            on_edit=lambda data: self.form_manager.open(None, data),
            on_delete=lambda fid: self.main_page.run_task(self._delete_flight, fid),
            on_clone=self._clone_flight,
            on_qr=lambda seg, owner: self.qr_manager.open(seg, owner)
        )

        # UI
        self.outbound_list = ft.Column(spacing=15)
        self.inbound_list = ft.Column(spacing=15)
        self.loading = ft.ProgressBar(width=100, color=ft.Colors.CYAN, visible=False)
        
        self.filter_switch = ft.Switch(
            label="Ver Voos do Grupo", 
            value=False, 
            active_color=ft.Colors.CYAN,
            on_change=self._on_filter_change
        )

        self.btn_info = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE, 
            icon_color=ft.Colors.AMBER, 
            tooltip="Regras de Bagagem", 
            on_click=self.baggage_manager.show
        )
        
        self.add_outbound = ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN, tooltip="Novo Voo Ida", on_click=lambda e: self.form_manager.open("ida"))
        self.add_inbound = ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN, tooltip="Novo Voo Volta", on_click=lambda e: self.form_manager.open("volta"))

        self.controls = [
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Container(self.loading, alignment=ft.Alignment(0,0), height=5),
                    ft.Row([ft.Row([ft.Text("Mural de Voos", size=24, weight="bold"), self.btn_info]), self.filter_switch], alignment="spaceBetween"),
                    ft.Divider(color=ft.Colors.GREY_800),
                    ft.Row([ft.Text("Ida (Outbound)", size=18, weight="bold", color=ft.Colors.CYAN), self.add_outbound], alignment="spaceBetween"),
                    self.outbound_list,
                    ft.Container(height=30),
                    ft.Row([ft.Text("Volta (Inbound)", size=18, weight="bold", color=ft.Colors.CYAN), self.add_inbound], alignment="spaceBetween"),
                    self.inbound_list,
                    ft.Container(height=100)
                ])
            )
        ]

    def did_mount(self):
        self.load_data()

    def load_data(self):
        self.loading.visible = True
        self.update()
        self.main_page.run_task(self._fetch_data)

    def _on_filter_change(self, e):
        self._render_lists()

    async def _fetch_data(self):
        try:
            self.flights = await FlightService.get_flights()
            self._render_lists()
        except Exception as e:
            print(f"Erro fetch: {e}")
        finally:
            self.loading.visible = False
            self.update()

    def _render_lists(self):
        visible = self.flights
        if not self.filter_switch.value:
            visible = [f for f in self.flights if str(f.get("user_id")) == str(self.user["id"])]

        ida = [f for f in visible if f.get("type") == "ida"]
        volta = [f for f in visible if f.get("type") == "volta"]
        
        self.outbound_list.controls = [self.card_manager.create_card(f) for f in ida] or [ft.Container(padding=15, content=ft.Text("Nenhum voo encontrado.", color=ft.Colors.GREY, italic=True))]
        self.inbound_list.controls = [self.card_manager.create_card(f) for f in volta] or [ft.Container(padding=15, content=ft.Text("Nenhum voo encontrado.", color=ft.Colors.GREY, italic=True))]
        self.update()

    def _clone_flight(self, source_data):
        new_data = copy.deepcopy(source_data)
        new_data["id"] = None
        new_data["user_id"] = self.user["id"]
        new_data["user_name"] = self.user["name"]
        
        # LIMPEZA OBRIGATÓRIA DE DADOS PESSOAIS NO CLONE
        for seg in new_data.get("segments", []):
            seg["seat"] = ""
            seg["raw_code"] = "" 
        
        self.form_manager.open(type_key=new_data.get("type"), flight_data=new_data, is_cloning=True)
        self.main_page.snack_bar = ft.SnackBar(ft.Text("Voo clonado! Preencha seu assento."), bgcolor=ft.Colors.BLUE); self.main_page.snack_bar.open = True; self.main_page.update()

    async def _delete_flight(self, fid):
        await FlightService.delete_flight(fid)
        self.load_data()