import flet as ft
from src.ui.components.smart_banner import SmartBanner 
# Importando os novos módulos separados
from src.ui.components.qg.header import QGHeader
from src.ui.components.qg.radar import QGRadar
from src.ui.components.qg.countries import QGCountries
from src.ui.components.qg.profile_sheet import QGProfileSheetManager
from src.ui.components.qg.status_dialog import StatusDialogManager

class QGContent(ft.Column):
    def __init__(self, page: ft.Page, navigate_to_country):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page
        self.user = self.main_page.user_profile
        self.navigate_to_country = navigate_to_country
        
        # --- Gerenciadores de Estado ---
        self.status_manager = StatusDialogManager(self.main_page, self.user, self._refresh_radar)
        self.profile_manager = QGProfileSheetManager(self.main_page, self.user, self.status_manager)
        
        # --- UI COMPONENTS ---
        self.header = QGHeader(self.user, self.profile_manager.open_profile)
        self.banner = SmartBanner(self.main_page, self.user)
        self.radar = QGRadar(self.main_page, self.user, self.profile_manager.open_profile)
        self.countries = QGCountries(self.navigate_to_country)

        # --- LAYOUT PRINCIPAL ---
        self.controls = [
            ft.Container(
                padding=ft.padding.only(left=20, right=20, top=10, bottom=30),
                content=ft.Column([
                    self.header,
                    ft.Container(height=10),
                    self.banner, 
                    ft.Container(height=20),
                    self.radar,
                    ft.Container(height=20),
                    ft.Text("Roteiros", weight="bold", size=18),
                    self.countries,
                    ft.Container(height=20),
                    ft.Container(
                        padding=15, bgcolor=ft.Colors.GREY_900, border_radius=10,
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.YELLOW),
                            ft.Text("Dica: Clique no seu ícone para atualizar onde você está.", size=12, color=ft.Colors.GREY)
                        ])
                    ),
                    ft.Container(height=50)
                ])
            )
        ]

    async def _refresh_radar(self):
        # Callback usado pelo StatusDialog para forçar atualização do radar
        await self.radar._load_profiles_radar()

    def did_mount(self):
        self.main_page.on_resized = self.profile_manager.handle_resize
        
        if hasattr(self.banner, "did_mount"):
            self.banner.did_mount()
        
        self.radar.start_loop()

    def will_unmount(self):
        self.radar.stop_loop()
        
        if hasattr(self.banner, "will_unmount"):
            self.banner.will_unmount()
            
        self.profile_manager.cleanup()
        self.main_page.update()