# ARQUIVO: src/ui/components/utilities/quick_access.py
import flet as ft
from datetime import datetime, time
from src.logic.place_service import PlaceService

class QuickAccessButton(ft.FloatingActionButton):
    def __init__(self, page: ft.Page, user_profile: dict = None):
        super().__init__()
        self.page_ref = page
        self.profile = user_profile or {} 
        
        self.icon = ft.Icons.LOCAL_POLICE_OUTLINED
        self.bgcolor = ft.Colors.RED_700
        self.tooltip = "Acesso Rápido - Dados de Viagem"
        self.on_click = self._open_dialog_safe
        
        # --- ESTADO LOCAL ---
        self.user_data = {
            "placa": "", "doc_num": "", "hotel": "Carregando...", 
            "seguro": "", "emergencia": "", "sangue": ""
        }
        
        self.content_switcher = ft.AnimatedSwitcher(
            content=ft.Container(),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
            reverse_duration=300
        )

        # CRIA O DIÁLOGO UMA ÚNICA VEZ (SINGLETON)
        self.dialog = ft.AlertDialog(
            content=ft.Container(
                content=self.content_switcher,
                width=400, height=650, 
                bgcolor=ft.Colors.GREY_900, 
                border=ft.border.all(1, ft.Colors.CYAN_900),
                border_radius=15,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK)
            ),
            content_padding=0,
            modal=True, # Bloqueia o fundo
            bgcolor=ft.Colors.TRANSPARENT,
            actions=[], # Sem botões padrão do sistema
        )

    def did_mount(self):
        # Carrega dados silenciosamente
        self.page_ref.run_task(self._load_data)

    # --- LÓGICA DE DADOS (Mantida igual) ---
    async def _get_smart_accommodation(self):
        try:
            now = datetime.now()
            current_time = now.time()
            checkout_limit = time(12, 0) 
            countries = ["BR", "AR", "PY"] 
            for code in countries:
                try:
                    places = await PlaceService.get_places(code, "hotel")
                    if not places: continue 
                    for p in places:
                        c_in, c_out = p.get("check_in"), p.get("check_out")
                        if c_in and c_out:
                            d_in = datetime.strptime(c_in, "%Y-%m-%d").date()
                            d_out = datetime.strptime(c_out, "%Y-%m-%d").date()
                            today = now.date()
                            if d_in <= today < d_out:
                                return f"{p.get('name')} ({code})\n{p.get('address')}"
                except: continue
        except: return None
        return None

    async def _load_data(self):
        try:
            smart_hotel = await self._get_smart_accommodation()
            p = self.profile
            medical = p.get("medical", {})
            contact = p.get("contact", {})
            plan = medical.get("health_plan", {})
            
            self.user_data["doc_num"] = p.get("passport") or p.get("rg") or ""
            self.user_data["sangue"] = medical.get("blood_type", "")
            
            plan_name = plan.get("name", "")
            plan_num = plan.get("number", "")
            self.user_data["seguro"] = f"{plan_name} - {plan_num}" if plan_name else ""
            
            emerg_name = contact.get("emergency_name", "")
            emerg_phone = contact.get("emergency_phone", "")
            self.user_data["emergencia"] = f"{emerg_name} ({emerg_phone})" if emerg_name else ""
            
            if hasattr(self.page_ref, 'client_storage'):
                cs = self.page_ref.client_storage
                self.user_data["placa"] = cs.get("qa_placa") or ""
                self.user_data["hotel"] = smart_hotel or cs.get("qa_hotel") or "Não definido"
                
                if not self.user_data["doc_num"]: self.user_data["doc_num"] = cs.get("qa_doc_num") or ""
                if not self.user_data["sangue"]: self.user_data["sangue"] = cs.get("qa_sangue") or ""
                if not self.user_data["seguro"]: self.user_data["seguro"] = cs.get("qa_seguro") or ""
                if not self.user_data["emergencia"]: self.user_data["emergencia"] = cs.get("qa_emergencia") or ""
        except: pass

    def _save_data(self, e):
        self.user_data["placa"] = self.tf_placa.value.upper()
        self.user_data["doc_num"] = self.tf_doc.value.upper()
        self.user_data["hotel"] = self.tf_hotel.value 
        self.user_data["seguro"] = self.tf_seguro.value
        self.user_data["emergencia"] = self.tf_emergencia.value
        self.user_data["sangue"] = self.tf_sangue.value.upper()
        
        try:
            if hasattr(self.page_ref, 'client_storage'):
                cs = self.page_ref.client_storage
                cs.set("qa_placa", self.user_data["placa"])
                cs.set("qa_doc_num", self.user_data["doc_num"])
                cs.set("qa_hotel", self.user_data["hotel"])
                cs.set("qa_seguro", self.user_data["seguro"])
                cs.set("qa_emergencia", self.user_data["emergencia"])
                cs.set("qa_sangue", self.user_data["sangue"])
        except: pass
        self._switch_to_display()

    # --- UI COMPONENTS ---

    def _build_info_card(self, label, value, icon, color=ft.Colors.WHITE, is_plate=False):
        val_text = value if value else "---"
        if is_plate:
            return ft.Container(
                content=ft.Column([
                    ft.Container(bgcolor=ft.Colors.BLUE_900, height=20, width=float('inf'), border_radius=ft.border_radius.only(top_left=8, top_right=8), content=ft.Text("BRASIL", size=10, weight="bold", color=ft.Colors.WHITE, text_align="center")),
                    ft.Container(padding=10, alignment=ft.Alignment(0,0), content=ft.Text(val_text, size=36, weight="bold", font_family="monospace", color=ft.Colors.BLACK))
                ], spacing=0),
                bgcolor=ft.Colors.WHITE, border=ft.border.all(2, ft.Colors.BLACK), border_radius=10, margin=ft.margin.only(bottom=15)
            )
        return ft.Container(
            content=ft.Row([
                ft.Container(content=ft.Icon(icon, color=ft.Colors.BLACK, size=24), padding=10, bgcolor=ft.Colors.with_opacity(0.8, color), border_radius=8),
                ft.Column([ft.Text(label.upper(), size=10, color=ft.Colors.GREY_500, weight="bold"), ft.Text(val_text, size=16, weight="bold", color=ft.Colors.WHITE, selectable=True)], spacing=2, expand=True)
            ]),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), border=ft.border.all(1, ft.Colors.WHITE10), border_radius=12, padding=10, margin=ft.margin.only(bottom=10)
        )
    
    def _build_blood_card(self, blood_type):
        return ft.Container(
            content=ft.Column([ft.Icon(ft.Icons.BLOODTYPE, color=ft.Colors.WHITE, size=20), ft.Text(blood_type if blood_type else "?", size=24, weight="bold", color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
            bgcolor=ft.Colors.RED_900, border=ft.border.all(2, ft.Colors.RED_500), border_radius=12, padding=5, alignment=ft.Alignment(0,0)
        )

    def _build_display_view(self):
        return ft.Container(
            padding=20,
            content=ft.Column([
                # CABEÇALHO LIMPO (Apenas título e editar)
                ft.Row([
                    ft.Icon(ft.Icons.SHIELD, color=ft.Colors.CYAN, size=30),
                    ft.Column([ft.Text("TRIPHUB SECURITY", size=10, color=ft.Colors.CYAN, weight="bold"), ft.Text("DADOS DO VIAJANTE", size=18, weight="bold", color=ft.Colors.WHITE)], spacing=0),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.GREY_400, on_click=lambda e: self._switch_to_edit(), tooltip="Editar"),
                ]),
                
                ft.Divider(color=ft.Colors.WHITE10),
                
                ft.Container(
                    expand=True,
                    content=ft.Column([
                        ft.Text("VEÍCULO", size=12, color=ft.Colors.CYAN_200, weight="bold"),
                        self._build_info_card("Placa", self.user_data["placa"], ft.Icons.DIRECTIONS_CAR, ft.Colors.CYAN, is_plate=True),
                        ft.Text("IDENTIFICAÇÃO", size=12, color=ft.Colors.CYAN_200, weight="bold"),
                        ft.Row([ft.Container(expand=3, content=self._build_info_card("Documento", self.user_data["doc_num"], ft.Icons.FINGERPRINT, ft.Colors.ORANGE)), ft.Container(width=10), ft.Container(width=80, height=80, content=self._build_blood_card(self.user_data["sangue"]))], vertical_alignment=ft.CrossAxisAlignment.START),
                        ft.Text("LOGÍSTICA", size=12, color=ft.Colors.CYAN_200, weight="bold"),
                        self._build_info_card("Hospedagem", self.user_data["hotel"], ft.Icons.HOTEL, ft.Colors.BLUE),
                        self._build_info_card("Seguro", self.user_data["seguro"], ft.Icons.HEALTH_AND_SAFETY, ft.Colors.GREEN),
                        self._build_info_card("Emergência", self.user_data["emergencia"], ft.Icons.PHONE_IN_TALK, ft.Colors.RED),
                    ], scroll=ft.ScrollMode.HIDDEN)
                ),

                # RODAPÉ COM BOTÃO DE FECHAR ÚNICO E ROBUSTO
                ft.Container(height=10),
                ft.TextButton(
                    "Fechar", 
                    icon=ft.Icons.CLOSE, 
                    width=float('inf'),
                    style=ft.ButtonStyle(color=ft.Colors.WHITE54, padding=20),
                    on_click=self._close_dialog_safe # Chama a função segura
                )
            ])
        )

    def _build_edit_view(self):
        def field_style(label, val, icon, lines=1):
            return ft.TextField(
                label=label, value=val, prefix_icon=icon, text_size=16,
                bgcolor=ft.Colors.BLACK45, border_color=ft.Colors.WHITE24,
                border_radius=10, multiline=(lines > 1), min_lines=lines
            )
        self.tf_placa = field_style("Placa", self.user_data["placa"], ft.Icons.DIRECTIONS_CAR)
        self.tf_doc = field_style("Documento", self.user_data["doc_num"], ft.Icons.BADGE)
        self.tf_sangue = field_style("Tipo Sanguíneo", self.user_data["sangue"], ft.Icons.BLOODTYPE)
        self.tf_hotel = field_style("Hotel", self.user_data["hotel"], ft.Icons.MAP, lines=2)
        self.tf_seguro = field_style("Seguro", self.user_data["seguro"], ft.Icons.GPP_GOOD)
        self.tf_emergencia = field_style("Emergência", self.user_data["emergencia"], ft.Icons.CONTACT_PHONE)

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([ft.Text("EDITAR DADOS", size=18, weight="bold", color=ft.Colors.WHITE), ft.Container(expand=True), ft.IconButton(ft.Icons.CLOSE, icon_color=ft.Colors.GREY, on_click=lambda e: self._switch_to_display())]),
                ft.Divider(color=ft.Colors.WHITE10),
                ft.Column([
                    ft.Row([ft.Container(expand=2, content=self.tf_placa), ft.Container(expand=1, content=self.tf_sangue)]),
                    self.tf_doc, self.tf_hotel, self.tf_seguro, self.tf_emergencia,
                ], scroll=ft.ScrollMode.HIDDEN, expand=True),
                ft.ElevatedButton("SALVAR", icon=ft.Icons.SAVE, bgcolor=ft.Colors.CYAN_800, color=ft.Colors.WHITE, width=float('inf'), on_click=self._save_data)
            ])
        )

    def _switch_to_display(self):
        self.content_switcher.content = self._build_display_view()
        self.content_switcher.update()

    def _switch_to_edit(self):
        self.content_switcher.content = self._build_edit_view()
        self.content_switcher.update()

    # --- ABERTURA E FECHAMENTO BLINDADOS ---

    async def _open_dialog_safe(self, e):
        """
        Abre o diálogo de forma segura.
        Remove qualquer instância anterior do overlay antes de adicionar a atual.
        """
        # 1. Limpeza Preventiva: Remove o diálogo se ele já estiver no overlay (lixo de sessão anterior)
        if self.dialog in self.page_ref.overlay:
            self.page_ref.overlay.remove(self.dialog)
        
        # 2. Atualiza dados e visual
        await self._load_data()
        self.content_switcher.content = self._build_display_view()

        # 3. Adiciona e abre
        self.page_ref.overlay.append(self.dialog)
        self.dialog.open = True
        self.page_ref.update()

    def _close_dialog_safe(self, e):
        """
        Fecha o diálogo APENAS visualmente.
        NÃO remove do overlay aqui para evitar erro de referência perdida.
        A remoção acontecerá apenas na próxima abertura (Limpeza Preventiva).
        """
        self.dialog.open = False
        self.page_ref.update()