import flet as ft
from src.logic.auth_service import AuthService

class MedicalContent(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page
        self.user = self.main_page.user_profile
        
        # Carrega dados
        saved_data = self.user.get("medical", {})
        self.med_data = AuthService.TEMPLATE_MEDICAL.copy()
        self.med_data.update(saved_data)
        
        # Sub-dicionários de segurança
        if "health_plan" not in self.med_data: self.med_data["health_plan"] = {"active": False, "name": "", "number": "", "phone": ""}
        if "funeral_plan" not in self.med_data: self.med_data["funeral_plan"] = {"active": False, "name": "", "phone": ""}
        if "doctor" not in self.med_data: self.med_data["doctor"] = {"name": "", "phone": ""}

        # --- SEÇÃO 1: DADOS VITAIS ---
        self.blood_type = ft.Dropdown(
            label="Tipo Sanguíneo",
            value=self.med_data.get("blood_type", "Não sei"),
            options=[ft.dropdown.Option(x) for x in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Não sei"]],
            expand=True, border_color=ft.Colors.RED_400
        )
        self.donor_switch = ft.Switch(
            label="Doador de Órgãos",
            value=self.med_data.get("donor", False),
            active_color=ft.Colors.RED_400
        )

        # --- SEÇÃO 2: CLÍNICO ---
        # Novo: Médico de Referência
        doc_data = self.med_data.get("doctor", {})
        self.doc_name = ft.TextField(label="Nome do Médico", value=doc_data.get("name", ""), icon=ft.Icons.MEDICAL_SERVICES, expand=True)
        self.doc_phone = ft.TextField(label="Tel. Médico", value=doc_data.get("phone", ""), icon=ft.Icons.PHONE, keyboard_type=ft.KeyboardType.PHONE, width=150)

        self.allergies = ft.TextField(label="Alergias (Alimentos/Remédios)", value=self.med_data.get("allergies", ""), multiline=True, icon=ft.Icons.WARNING_AMBER, border_color=ft.Colors.ORANGE_400)
        self.medications = ft.TextField(label="Medicamentos Contínuos", value=self.med_data.get("medications", ""), multiline=True, icon=ft.Icons.MEDICATION)
        self.vaccines = ft.TextField(label="Vacinas Recentes (Febre Amarela/COVID)", value=self.med_data.get("vaccines", ""), icon=ft.Icons.VACCINES)
        self.notes = ft.TextField(label="Histórico / Cirurgias / Doenças", value=self.med_data.get("notes", ""), multiline=True, icon=ft.Icons.NOTE_ADD)

        # --- SEÇÃO 3: SEGURO SAÚDE ---
        hp_data = self.med_data["health_plan"]
        self.hp_active = ft.Switch(label="Possuo Seguro Saúde/Viagem", value=hp_data.get("active"), on_change=self._toggle_health_fields)
        self.hp_name = ft.TextField(label="Seguradora / Plano", value=hp_data.get("name"), visible=hp_data.get("active"))
        self.hp_number = ft.TextField(label="Nº Apólice / Carteirinha", value=hp_data.get("number"), visible=hp_data.get("active"))
        self.hp_phone = ft.TextField(label="Tel. Emergência 24h", value=hp_data.get("phone"), keyboard_type=ft.KeyboardType.PHONE, visible=hp_data.get("active"))

        # --- SEÇÃO 4: PLANO FUNERÁRIO ---
        fp_data = self.med_data["funeral_plan"]
        self.fp_active = ft.Switch(label="Possuo Plano Funerário", value=fp_data.get("active"), on_change=self._toggle_funeral_fields)
        self.fp_name = ft.TextField(label="Empresa / Plano", value=fp_data.get("name"), visible=fp_data.get("active"))
        self.fp_phone = ft.TextField(label="Telefone de Acionamento", value=fp_data.get("phone"), keyboard_type=ft.KeyboardType.PHONE, visible=fp_data.get("active"))

        # --- MONTAGEM DO LAYOUT ---
        self.controls = [
            ft.Container(
                padding=20,
                content=ft.Column([
                    # Cabeçalho
                    ft.Container(
                        bgcolor=ft.Colors.RED_900, border_radius=15, padding=20, width=float("inf"),
                        content=ft.Row([
                            ft.Icon(ft.Icons.MEDICAL_INFORMATION, size=30, color=ft.Colors.WHITE),
                            ft.Text("FICHA DE EMERGÊNCIA", size=18, weight="bold", color=ft.Colors.WHITE)
                        ], alignment="center")
                    ),
                    ft.Container(height=10),

                    # Card Vitais
                    self._build_card("DADOS VITAIS", [
                        ft.Row([self.blood_type, self.donor_switch], alignment="spaceBetween")
                    ]),

                    # Card Clínico
                    self._build_card("QUADRO CLÍNICO & PROFISSIONAIS", [
                        ft.Text("Médico de Referência:", color=ft.Colors.CYAN, size=12, weight="bold"),
                        ft.Row([self.doc_name, self.doc_phone]),
                        ft.Divider(color=ft.Colors.GREY_800),
                        self.allergies, 
                        self.medications, 
                        self.vaccines, 
                        self.notes
                    ]),

                    # Card Seguros
                    self._build_card("SEGUROS & ASSISTÊNCIA", [
                        self.hp_active, self.hp_name, self.hp_number, self.hp_phone,
                        ft.Divider(),
                        self.fp_active, self.fp_name, self.fp_phone
                    ], color=ft.Colors.BLUE_GREY_900),

                    ft.Container(height=20),
                    ft.ElevatedButton("SALVAR TUDO", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, height=50, width=float("inf"), on_click=self._save_medical_data),
                    ft.Container(height=50)
                ])
            )
        ]

    def _build_card(self, title, controls, color=ft.Colors.GREY_900):
        # CORREÇÃO DE LAYOUT: width=float("inf") força o card a ocupar toda a largura
        return ft.Container(
            bgcolor=color, 
            border_radius=15, 
            padding=20, 
            width=float("inf"), 
            content=ft.Column([
                ft.Text(title, weight="bold", color=ft.Colors.GREY_400, size=12),
                ft.Column(controls, spacing=15)
            ])
        )

    def _toggle_health_fields(self, e):
        visible = self.hp_active.value
        self.hp_name.visible = visible
        self.hp_number.visible = visible
        self.hp_phone.visible = visible
        self.update()

    def _toggle_funeral_fields(self, e):
        visible = self.fp_active.value
        self.fp_name.visible = visible
        self.fp_phone.visible = visible
        self.update()

    def _save_medical_data(self, e):
        self.med_data = {
            "blood_type": self.blood_type.value,
            "donor": self.donor_switch.value,
            "doctor": {"name": self.doc_name.value, "phone": self.doc_phone.value}, # Salva médico
            "allergies": self.allergies.value,
            "medications": self.medications.value,
            "vaccines": self.vaccines.value,
            "notes": self.notes.value,
            "health_plan": {
                "active": self.hp_active.value,
                "name": self.hp_name.value,
                "number": self.hp_number.value,
                "phone": self.hp_phone.value
            },
            "funeral_plan": {
                "active": self.fp_active.value,
                "name": self.fp_name.value,
                "phone": self.fp_phone.value
            }
        }
        
        self.main_page.run_task(self._persist_save)

    async def _persist_save(self):
        if await AuthService.update_profile_general(self.user["id"], {"medical": self.med_data}):
            self.user["medical"] = self.med_data
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Ficha Médica atualizada!"), bgcolor=ft.Colors.GREEN_700)
        else:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("Erro ao salvar."), bgcolor=ft.Colors.RED_700)
        
        self.main_page.snack_bar.open = True
        self.main_page.update()