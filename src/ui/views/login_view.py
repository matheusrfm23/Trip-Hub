# ARQUIVO: src/ui/views/login_view.py
import flet as ft
import logging
from src.logic.auth_service import AuthService

logger = logging.getLogger("TripHub.Login")

class LoginView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/login")
        self.main_page = page
        self.bgcolor = ft.Colors.BLACK
        self.padding = 0
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        self.selected_profile = None

        # --- UI ELEMENTS ---
        self.profiles_row = ft.Row(
            wrap=True, 
            alignment=ft.MainAxisAlignment.CENTER, 
            spacing=30,
            run_spacing=30,
            width=700
        )
        
        self.loader = ft.ProgressRing(color=ft.Colors.CYAN, visible=True)

        self.pin_field = ft.TextField(
            label="PIN", 
            password=True, 
            can_reveal_password=True, 
            text_align="center", 
            width=180, 
            max_length=4,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ft.Colors.CYAN,
            text_style=ft.TextStyle(size=24, weight="bold", letter_spacing=5),
            on_submit=self._verify_pin,
            autofocus=True 
        )
        self.pin_error = ft.Text("", color=ft.Colors.RED, size=12, weight="bold")

        self.pin_dialog = ft.AlertDialog(
            modal=False,
            on_dismiss=self._on_dialog_dismiss,
            title=ft.Row([ft.Icon(ft.Icons.LOCK), ft.Text("Acesso")], alignment="center"),
            content=ft.Container(
                height=140,
                content=ft.Column([
                    ft.Text("Digite seu PIN", color=ft.Colors.GREY),
                    self.pin_field,
                    self.pin_error
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
            ),
            actions=[
                ft.TextButton("Voltar", on_click=self._close_dialogs),
                ft.ElevatedButton("ENTRAR", on_click=self._verify_pin, bgcolor=ft.Colors.CYAN, color=ft.Colors.BLACK)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.new_name = ft.TextField(label="Nome") 
        self.new_pin = ft.TextField(label="PIN", max_length=4, keyboard_type=ft.KeyboardType.NUMBER)
        
        self.add_dialog = ft.AlertDialog(
            modal=False,
            on_dismiss=self._on_dialog_dismiss,
            title=ft.Text("Novo Viajante"),
            content=ft.Column([self.new_name, self.new_pin], height=150, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self._close_dialogs),
                ft.ElevatedButton("Salvar", on_click=self._save_profile, bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
            ]
        )

        self.scroll_container = ft.Container(
            height=500,
            padding=20,
            content=ft.Column(
                controls=[
                    self.profiles_row,
                    ft.Container(height=20),
                    self.loader
                ],
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        self.controls = [
            ft.Container(
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, 0), end=ft.Alignment(0, 1),
                    colors=[ft.Colors.BLUE_GREY_900, ft.Colors.BLACK]
                ),
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.AIRPLANE_TICKET, size=70, color=ft.Colors.CYAN),
                        ft.Text("TripHub", size=40, weight="bold", font_family="Verdana"),
                        ft.Container(
                            content=ft.Text("By: MatheusRFM", size=12, color=ft.Colors.CYAN_100, italic=True, weight="bold"),
                            margin=ft.margin.only(top=-5, bottom=10)
                        ),
                        ft.Text("Selecione seu perfil", size=16, color=ft.Colors.GREY),
                        ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                        self.scroll_container
                    ]
                )
            )
        ]

    def did_mount(self):
        self.main_page.run_task(self._load_profiles)

    async def _load_profiles(self):
        try:
            self.profiles_data = await AuthService.get_profiles()
            cards = []
            
            # Feedback visual caso não haja perfis
            if not self.profiles_data:
                cards.append(ft.Text("Nenhum perfil encontrado. Crie um!", color="yellow"))
            
            for p in self.profiles_data:
                cards.append(self._create_circular_profile(p))
            
            cards.append(self._create_add_button())
            self.profiles_row.controls = cards
        except Exception as e:
            logger.error(f"Erro ao carregar perfis: {e}")
            self.profiles_row.controls = [ft.Text(f"Erro de conexão: {e}", color="red")]
        
        self.loader.visible = False
        self.update()

    def _create_circular_profile(self, profile):
        initials = profile["name"][:2].upper()
        return ft.Column(
            controls=[
                ft.Container(
                    width=100, height=100,
                    border_radius=50,
                    bgcolor=ft.Colors.GREY_900,
                    border=ft.border.all(2, ft.Colors.CYAN_400),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(initials, size=30, weight="bold", color=ft.Colors.WHITE),
                    ink=True,
                    data=profile, 
                    on_click=self._on_profile_click
                ),
                ft.Text(profile["name"], size=16, weight="bold", color=ft.Colors.WHITE70, text_align="center")
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

    def _create_add_button(self):
        return ft.Column(
            [
                ft.Container(
                    width=100, height=100,
                    border_radius=50,
                    bgcolor=ft.Colors.BLACK,
                    border=ft.border.all(2, ft.Colors.GREY_800),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.ADD, size=40, color=ft.Colors.GREY),
                    ink=True,
                    on_click=self._open_add_dialog
                ),
                ft.Text("Adicionar", size=16, color=ft.Colors.GREY, text_align="center")
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

    async def _on_profile_click(self, e):
        self.selected_profile = e.control.data
        self.pin_field.value = ""
        self.pin_error.value = ""
        self.pin_field.disabled = False
        # [ATUALIZADO] Flet 0.80+ usa page.open(dialog)
        self.main_page.open(self.pin_dialog)
        self.main_page.update()
        try: await self.pin_field.focus()
        except: pass

    async def _verify_pin(self, e):
        if not self.pin_field.value: return
        self.pin_field.disabled = True
        self.update()

        # [MODIFICAÇÃO] Usa o AuthService para validar login e gerar logs
        user_id = self.selected_profile.get("id")
        pin = self.pin_field.value
        
        user = await AuthService.login(user_id, pin)

        if user:
            self.main_page.close(self.pin_dialog) # [ATUALIZADO]
            self.main_page.user_profile = user
            
            # --- BLINDAGEM DE STORAGE ---
            try:
                # Salva sessão no navegador (Flet Client Storage)
                if hasattr(self.main_page, "client_storage") and self.main_page.client_storage:
                    self.main_page.client_storage.set("user_id", str(user["id"]))
                
                # [REMOVIDO] AuthService.save_cached_login(user["id"])
                # A persistência agora é 100% responsabilidade do client_storage
            except Exception as ex:
                logger.warning(f"Não foi possível salvar sessão: {ex}")
            # ---------------------------
            
            # [CORREÇÃO CRÍTICA DE ROTA]
            if self.main_page.route == "/dashboard":
                logger.info("Rota presa em /dashboard detectada. Redirecionando via root.")
                self.main_page.go("/")
            else:
                self.main_page.go("/dashboard")
        else:
            self.pin_error.value = "Senha incorreta"
            self.pin_field.disabled = False
            self.pin_field.value = ""
            self.pin_field.focus()
            self.update()

    async def _open_add_dialog(self, e):
        self.new_name.value = ""
        self.new_pin.value = ""
        # [ATUALIZADO] Flet 0.80+ usa page.open(dialog)
        self.main_page.open(self.add_dialog)
        self.main_page.update()
        try: await self.new_name.focus()
        except: pass

    def _close_dialogs(self, e):
        # [ATUALIZADO] Flet 0.80+ usa page.close(dialog)
        self.main_page.close(self.pin_dialog)
        self.main_page.close(self.add_dialog)
        self.main_page.update()

    def _on_dialog_dismiss(self, e):
        self.pin_field.value = ""
        self.pin_error.value = ""
        self.selected_profile = None
        self.pin_field.disabled = False
        # self.main_page.overlay.clear() # Não necessário com page.close()
        self.main_page.update()

    async def _save_profile(self, e):
        if self.new_name.value and len(self.new_pin.value) == 4:
            self.main_page.close(self.add_dialog) # [ATUALIZADO]
            self.main_page.update()
            self.loader.visible = True
            self.update()
            await AuthService.create_profile(self.new_name.value, self.new_pin.value)
            await self._load_profiles()
