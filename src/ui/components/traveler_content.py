import flet as ft
from src.logic.auth_service import AuthService

class TravelerContent(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page
        self.user = self.main_page.user_profile
        
        # Carrega dados
        self.contact_data = self.user.get("contact", AuthService.TEMPLATE_CONTACT.copy())
        
        # --- CAMPOS ---
        self.name_field = ft.TextField(
            label="Nome Completo", 
            value=self.user.get("name", ""), 
            prefix_icon=ft.Icons.PERSON, 
            text_style=ft.TextStyle(weight="bold", size=16),
            border_color=ft.Colors.CYAN
        )
        
        # PIN agora tem largura fixa e fica sozinho na linha
        self.pin_field = ft.TextField(
            label="PIN de Acesso", 
            value=self.user.get("pin", ""), 
            password=True, 
            can_reveal_password=True, 
            max_length=4, 
            width=180, # Largura controlada
            prefix_icon=ft.Icons.LOCK_OUTLINE, 
            keyboard_type=ft.KeyboardType.NUMBER,
            text_align="center",
            text_style=ft.TextStyle(weight="bold", letter_spacing=5) # Espaçamento para ficar bonito
        )
        
        # Documentos
        self.passport_field = ft.TextField(label="Passaporte", value=self.user.get("passport", ""), prefix_icon=ft.Icons.BOOK, expand=True)
        self.cpf_field = ft.TextField(label="CPF", value=self.user.get("cpf", ""), prefix_icon=ft.Icons.BADGE, expand=True)
        self.rg_field = ft.TextField(label="RG", value=self.user.get("rg", ""), prefix_icon=ft.Icons.BADGE_OUTLINED, expand=True)
        
        # Contatos
        self.phone_field = ft.TextField(label="Celular", value=self.contact_data.get("phone", ""), prefix_icon=ft.Icons.PHONE_ANDROID, keyboard_type=ft.KeyboardType.PHONE)
        self.email_field = ft.TextField(label="E-mail", value=self.contact_data.get("email", ""), prefix_icon=ft.Icons.EMAIL)
        
        self.emer_name = ft.TextField(label="Contato Emergência", value=self.contact_data.get("emergency_name", ""), prefix_icon=ft.Icons.CONTACT_EMERGENCY, expand=True)
        self.emer_phone = ft.TextField(label="Tel. Emergência", value=self.contact_data.get("emergency_phone", ""), prefix_icon=ft.Icons.PHONE_CALLBACK, keyboard_type=ft.KeyboardType.PHONE, expand=True)

        privacy = self.user.get("privacy", {})
        self.share_passport = ft.Switch(label="Compartilhar Documentos", value=privacy.get("passport", False), active_color=ft.Colors.CYAN)
        
        self._setup_delete_dialog()

        # --- LAYOUT CORRIGIDO ---
        self.controls = [
            ft.Container(
                padding=15,
                content=ft.Column([
                    
                    # 1. CABEÇALHO
                    ft.Container(
                        bgcolor=ft.Colors.BLUE_GREY_900, border_radius=15, padding=15,
                        content=ft.Row([
                            ft.CircleAvatar(content=ft.Text(self.user["name"][0].upper()), radius=30, bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE),
                            ft.Column([
                                ft.Text(self.user["name"], size=20, weight="bold"),
                                ft.Text(f"PERFIL: {self.user['role']}", size=10, color=ft.Colors.CYAN_200, weight="bold")
                            ], spacing=2)
                        ])
                    ),
                    
                    ft.Container(height=10),

                    # 2. IDENTIDADE & SEGURANÇA (Layout Verticalizado)
                    self._build_card("ACESSO & SEGURANÇA", ft.Icons.SHIELD, [
                        self.name_field, # Nome em cima
                        ft.Container(height=5),
                        ft.Row([ # PIN e texto explicativo lado a lado ou PIN isolado
                            self.pin_field,
                            ft.Container(content=ft.Text("Seu PIN é sua chave.", color=ft.Colors.GREY, size=12), padding=10)
                        ])
                    ]),

                    ft.Container(height=10),

                    # 3. DOCUMENTAÇÃO
                    self._build_card("DOCUMENTAÇÃO", ft.Icons.FOLDER_SHARED, [
                        ft.Text("Internacional", size=12, color=ft.Colors.CYAN),
                        self.passport_field,
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Text("Nacional", size=12, color=ft.Colors.CYAN),
                        ft.Row([self.cpf_field, self.rg_field]),
                        ft.Divider(height=5, color=ft.Colors.GREY_800),
                        ft.Row([ft.Icon(ft.Icons.PRIVACY_TIP, size=16, color=ft.Colors.GREY), self.share_passport], alignment="spaceBetween")
                    ]),

                    ft.Container(height=10),

                    # 4. CONTATOS
                    self._build_card("CONTATOS", ft.Icons.CONTACT_PHONE, [
                        self.phone_field,
                        self.email_field,
                        ft.Divider(height=20, color=ft.Colors.GREY_800),
                        ft.Text("Em caso de emergência:", size=12, color=ft.Colors.RED_300, weight="bold"),
                        ft.Row([self.emer_name, self.emer_phone])
                    ]),

                    ft.Container(height=20),

                    # BOTÃO SALVAR
                    ft.ElevatedButton("ATUALIZAR DADOS", icon=ft.Icons.SAVE, width=float("inf"), height=50, 
                                      style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                                      on_click=self._save_data),

                    ft.Container(height=30),
                    
                    # ZONA DE PERIGO
                    ft.OutlinedButton("Excluir Minha Conta", icon=ft.Icons.DELETE_FOREVER, 
                                      style=ft.ButtonStyle(color=ft.Colors.RED_400, side=ft.BorderSide(1, ft.Colors.RED_900)), 
                                      width=float("inf"), on_click=self._open_delete_dialog),
                    
                    ft.Container(height=50)
                ])
            )
        ]

    def _build_card(self, title, icon, controls):
        return ft.Container(
            bgcolor=ft.Colors.GREY_900, border_radius=12, padding=15,
            content=ft.Column([
                ft.Row([ft.Icon(icon, size=18, color=ft.Colors.CYAN), ft.Text(title, weight="bold", color=ft.Colors.CYAN, size=12)], spacing=5),
                ft.Column(controls, spacing=10)
            ])
        )

    def _save_data(self, e):
        updated_contact = {
            "phone": self.phone_field.value,
            "email": self.email_field.value,
            "emergency_name": self.emer_name.value,
            "emergency_phone": self.emer_phone.value
        }
        updates = {
            "name": self.name_field.value,
            "pin": self.pin_field.value,
            "passport": self.passport_field.value,
            "cpf": self.cpf_field.value,
            "rg": self.rg_field.value,
            "privacy": {"passport": self.share_passport.value, "medical": True},
            "contact": updated_contact
        }
        self.main_page.run_task(self._persist_save, updates)

    async def _persist_save(self, updates):
        if await AuthService.update_profile_general(self.user["id"], updates):
            self.user.update(updates)
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Perfil salvo!"), bgcolor=ft.Colors.GREEN)
            self.main_page.snack_bar.open = True
            self.main_page.update()

    def _setup_delete_dialog(self):
        self.master_input = ft.TextField(label="Senha Mestra (1995)", password=True, text_align="center", height=40)
        self.delete_dialog = ft.AlertDialog(
            title=ft.Text("Excluir Conta?", color=ft.Colors.RED, size=16),
            content=ft.Container(height=70, content=ft.Column([
                ft.Text("Isso apagará perfil e voos. Irreversível.", size=12),
                ft.Container(height=5),
                self.master_input
            ])),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(self.delete_dialog, 'open', False) or self.main_page.update()),
                ft.ElevatedButton("CONFIRMAR EXCLUSÃO", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, on_click=self._confirm_delete)
            ]
        )

    def _open_delete_dialog(self, e):
        self.master_input.value = ""
        self.main_page.dialog = self.delete_dialog
        self.delete_dialog.open = True
        self.main_page.update()

    def _confirm_delete(self, e):
        if self.master_input.value == AuthService.MASTER_PIN:
            self.delete_dialog.open = False 
            self.main_page.update()         
            self.main_page.run_task(self._execute_delete)
        else:
            self.master_input.error_text = "Senha incorreta"
            self.delete_dialog.update()

    async def _execute_delete(self):
        # 1. Apaga do "Banco de Dados" (JSON)
        success = await AuthService.delete_profile(self.user["id"])
        
        if success:
            # 2. Feedback rápido
            print(f"Usuário {self.user['name']} deletado com sucesso.")
            
            # 3. Limpa a sessão local (memória)
            self.main_page.user_profile = None
            
            # 4. Redireciona
            self.main_page.go("/login")
        else:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Erro ao excluir. Tente novamente."), bgcolor=ft.Colors.RED)
            self.main_page.snack_bar.open = True
            self.main_page.update()