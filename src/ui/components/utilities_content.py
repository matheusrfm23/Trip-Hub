# ARQUIVO: src/ui/components/utilities_content.py
import flet as ft
from src.ui.components.utilities.tax_calculator import TaxCalculator
from src.ui.components.utilities.roulette import PlaceRoulette
from src.ui.components.utilities.checklist_panel import ChecklistPanel
from src.ui.components.utilities.info_hub import InfoHub
from src.logic.protocol_service import ProtocolService # <--- IMPORTANTE

class UtilitiesContent(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page 
        self.user_id = self.main_page.user_profile["id"]
        
        # --- VERIFICAÇÃO ROBUSTA DE LEITURA ---
        # Usa o serviço JSON (ProtocolService), não o cache do navegador
        self.is_unlocked = ProtocolService.has_read(self.user_id)

        # --- COMPONENTES ---
        self.info_hub = InfoHub(self.main_page, self._unlock_tools)
        
        # Ferramentas
        self.checklist = ChecklistPanel(self.main_page)
        self.calculator = TaxCalculator(self.main_page)
        self.roulette = PlaceRoulette(self.main_page)
        
        # Container das ferramentas
        self.tools_container = ft.Column(
            spacing=20,
            controls=[
                self._wrap_tool(self.checklist, "Checklist de Bagagem"),
                self._wrap_tool(self.calculator, "Calculadora Fiscal"),
                self._wrap_tool(self.roulette, "Roleta de Decisões")
            ]
        )
        
        self._apply_lock_state()

        self.content = ft.Column(
            scroll=ft.ScrollMode.HIDDEN,
            spacing=20,
            controls=[
                # --- CABEÇALHO ---
                ft.Container(
                    padding=ft.padding.only(top=20, left=20, right=20),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.BUILD_CIRCLE_OUTLINED, size=40, color=ft.Colors.CYAN),
                            ft.Column([
                                ft.Text("Utilidades & Regras", size=24, weight="bold"),
                                ft.Text("Centro de Controle Logístico", size=12, color=ft.Colors.GREY),
                            ], spacing=2)
                        ]),
                        ft.Divider(color=ft.Colors.WHITE10),
                    ])
                ),
                
                # --- 1. PROTOCOLOS (Obrigatório) ---
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20),
                    content=self.info_hub
                ),

                # --- 2. FERRAMENTAS (Bloqueáveis) ---
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20),
                    content=self.tools_container
                ),
                
                # Espaço extra
                ft.Container(height=100) 
            ]
        )

    def _wrap_tool(self, control, name):
        """Envolve a ferramenta para facilitar o bloqueio visual"""
        return ft.Container(
            content=ft.Stack([
                control,
                # Overlay de Bloqueio
                ft.Container(
                    visible=not self.is_unlocked,
                    bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
                    alignment=ft.Alignment(0,0),
                    content=ft.Column([
                        ft.Icon(ft.Icons.LOCK_OUTLINE, size=40, color=ft.Colors.GREY),
                        ft.Text(f"Leia os protocolos para liberar", color=ft.Colors.GREY),
                        ft.Text(name, size=12, color=ft.Colors.GREY_700, weight="bold")
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                    border_radius=15,
                )
            ])
        )

    def _apply_lock_state(self):
        """Aplica o estado visual de bloqueio/desbloqueio"""
        for container in self.tools_container.controls:
            overlay = container.content.controls[1]
            overlay.visible = not self.is_unlocked
            
            real_control = container.content.controls[0]
            real_control.disabled = not self.is_unlocked
            real_control.opacity = 0.2 if not self.is_unlocked else 1.0

    def _unlock_tools(self):
        self.is_unlocked = True
        self._apply_lock_state()
        self.tools_container.update()