import flet as ft
import time
from datetime import datetime, timedelta
from src.logic.auth_service import AuthService
from src.logic.finance_service import FinanceService
from src.logic.flight_service import FlightService 
from src.logic.chat_service import ChatService 
from src.ui.components.chat_content import ChatContent

class QGProfileSheetManager:
    def __init__(self, page: ft.Page, user, status_manager):
        self.page = page
        self.user = user
        self.status_manager = status_manager # Para chamar o handle_gps_click
        self.is_chat_active = False
        
        self.sheet_content = ft.Container()
        self.bottom_sheet = ft.BottomSheet(
            content=self.sheet_content,
            bgcolor=ft.Colors.GREY_900,
            on_dismiss=self._on_sheet_dismiss
        )

        self.confirm_delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ ZONA DE PERIGO ⚠️", color=ft.Colors.RED),
            content=ft.Text("Tem certeza? Esta ação apagará permanentemente o seu Perfil, Voos e Finanças e não tem volta."),
            actions=[
                ft.TextButton("Cancelar", on_click=self._close_delete_dialog),
                ft.ElevatedButton(
                    "SIM, APAGAR TUDO",
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: self.page.run_task(self._delete_task)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def cleanup(self):
        # Limpeza segura do overlay
        if self.bottom_sheet in self.page.overlay:
            self.page.overlay.remove(self.bottom_sheet)
        if self.confirm_delete_dialog in self.page.overlay:
            self.page.overlay.remove(self.confirm_delete_dialog)

    def handle_resize(self, height):
        if self.is_chat_active and self.bottom_sheet.open:
            new_height = float(height) - 10
            self.sheet_content.height = new_height
            self.sheet_content.update()

    def _on_sheet_dismiss(self, e):
        # Se for fechado via clique fora, garante que o estado de open reflita
        self.bottom_sheet.open = False
        self.is_chat_active = False 
        self.page.update()

    def open_profile(self, profile):
        self.is_chat_active = False 
        self.page.run_task(self._build_main_profile_view, profile)

    async def _build_main_profile_view(self, profile):
        is_me = str(profile["id"]) == str(self.user["id"])
        
        now = time.time()
        last_seen = profile.get("last_seen", 0)
        is_online = (now - last_seen) < 300
        
        status_text = "Online agora" if is_online else f"Visto há {int((now-last_seen)/60)} min"
        if is_me: status_text = "Você (Online)"
        
        custom_msg = profile.get("status_msg", "Disponível")
        status_color = ft.Colors.GREEN if is_online else ft.Colors.GREY
        
        header = ft.Row([
            ft.CircleAvatar(content=ft.Text(profile["name"][:2].upper()), radius=35, bgcolor=ft.Colors.CYAN_900, color=ft.Colors.WHITE),
            ft.Column([
                ft.Text(profile["name"], size=22, weight="bold"),
                ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, size=10, color=status_color),
                    ft.Text(status_text, size=12, color=ft.Colors.GREY_400)
                ], spacing=5),
                ft.Text(f'"{custom_msg}"', size=13, italic=True, color=ft.Colors.CYAN_200)
            ], spacing=2, expand=True),
            
            ft.IconButton(
                ft.Icons.EDIT_LOCATION if is_me else ft.Icons.MAP, 
                icon_color=ft.Colors.CYAN, 
                tooltip="Localização",
                on_click=lambda e: self.status_manager.handle_click(profile)
            )
        ])

        # --- ADMIN PANEL ---
        admin_compact_switch = ft.Container()
        if self.user.get("role") == "ADMIN" and not is_me:
            is_target_admin = profile.get("role") == "ADMIN"
            admin_compact_switch = ft.Row([
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    content=ft.Row([
                        ft.Icon(ft.Icons.SECURITY, size=14, color=ft.Colors.ORANGE),
                        ft.Text("Admin", size=12, weight="bold"), 
                        ft.Switch(
                            value=is_target_admin,
                            active_color=ft.Colors.ORANGE,
                            scale=0.7,
                            on_change=lambda e: self.page.run_task(self._update_user_role, profile, e.control.value)
                        )
                    ], spacing=5, alignment="center")
                )
            ], alignment=ft.MainAxisAlignment.END)

        # --- STATUS DE VOO ---
        flight_widget = await self._build_flight_status_widget(profile)

        # Resumo Financeiro
        fin_widget = ft.Container()
        if not is_me:
            balance = await FinanceService.get_p2p_status(self.user["id"], profile["id"])
            if balance > 0.01:
                fin_txt, fin_col, fin_ico = f"Te deve: R$ {balance:,.2f}", ft.Colors.GREEN_400, ft.Icons.TRENDING_UP
            elif balance < -0.01:
                fin_txt, fin_col, fin_ico = f"Você deve: R$ {abs(balance):,.2f}", ft.Colors.RED_400, ft.Icons.TRENDING_DOWN
            else:
                fin_txt, fin_col, fin_ico = "Tudo quitado!", ft.Colors.GREY_400, ft.Icons.CHECK_CIRCLE
            
            fin_widget = ft.Container(
                bgcolor=ft.Colors.BLACK26, padding=10, border_radius=10, margin=ft.margin.only(bottom=10),
                content=ft.Row([ft.Icon(fin_ico, color=fin_col), ft.Text(fin_txt, color=fin_col, weight="bold", size=16)], alignment=ft.MainAxisAlignment.CENTER)
            )

        # --- BADGE ---
        unread_count = 0
        if not is_me:
            unread_count = await ChatService.get_unread_from(self.user["id"], profile["id"])

        grid_buttons = ft.GridView(
            runs_count=2, 
            max_extent=180, 
            child_aspect_ratio=2.5,
            spacing=10, 
            run_spacing=10,
            controls=[
                self._build_action_tile("Saúde", ft.Icons.MEDICAL_SERVICES, ft.Colors.RED_900, lambda e: self._navigate_to_view(profile, "medical")),
                self._build_action_tile("Documentos", ft.Icons.ARTICLE, ft.Colors.BLUE_900, lambda e: self._navigate_to_view(profile, "docs")),
                self._build_action_tile("Contatos", ft.Icons.PHONE, ft.Colors.GREEN_900, lambda e: self._navigate_to_view(profile, "contact")),
                self._build_action_tile(
                    "Direct", 
                    ft.Icons.CHAT, 
                    ft.Colors.TEAL_800, 
                    lambda e: self._navigate_to_chat(profile), 
                    disabled=False,
                    badge_count=unread_count
                ),
            ]
        )

        # --- BOTÃO DE EXCLUSÃO (Seguro) ---
        delete_section = ft.Container()
        if is_me:
            delete_section = ft.Container(
                margin=ft.margin.only(top=30, bottom=20),
                alignment=ft.Alignment(0, 0),
                content=ft.TextButton(
                    "Excluir Conta Permanentemente",
                    icon=ft.Icons.DELETE_FOREVER,
                    icon_color=ft.Colors.RED,
                    style=ft.ButtonStyle(color=ft.Colors.RED, overlay_color=ft.Colors.RED_900),
                    on_click=self._confirm_delete_profile
                )
            )

        self.sheet_content.content = ft.Container(
            padding=20, 
            height=850, 
            content=ft.Column([
                ft.Container(width=40, height=4, bgcolor=ft.Colors.GREY_600, border_radius=2, margin=ft.margin.only(bottom=15), alignment=ft.Alignment(0, 0)),
                header,
                admin_compact_switch,
                ft.Divider(color=ft.Colors.GREY_800),
                flight_widget, 
                fin_widget,
                ft.Text("Acessar Informações:", weight="bold", color=ft.Colors.GREY_400),
                grid_buttons,
                delete_section # [ATUALIZADO]
            ], scroll=ft.ScrollMode.AUTO)
        )
        
        self.sheet_content.height = 850 
        
        # [REGRAS DE OURO] Append ao overlay
        if self.bottom_sheet not in self.page.overlay: self.page.overlay.append(self.bottom_sheet)
        self.bottom_sheet.open = True
        self.page.update()

    def _confirm_delete_profile(self, e):
        # [REGRAS DE OURO] Append ao overlay
        if self.confirm_delete_dialog not in self.page.overlay:
            self.page.overlay.append(self.confirm_delete_dialog)
        self.confirm_delete_dialog.open = True
        self.page.update()

    def _close_delete_dialog(self, e):
        self.confirm_delete_dialog.open = False
        self.page.update()

    async def _delete_task(self):
        self.confirm_delete_dialog.open = False
        self.bottom_sheet.open = False
        self.page.update()

        # Exclui do banco
        await AuthService.delete_profile(self.user["id"])

        # Remove sessão do client_storage
        try:
            if self.page.client_storage:
                self.page.client_storage.remove("user_id")
        except: pass

        # Redireciona para login e limpa
        self.page.views.clear()
        await self.page.push_route("/login")

    def _navigate_to_chat(self, target_profile):
        self.page.run_task(ChatService.mark_conversation_as_read, self.user["id"], target_profile["id"])
        self.is_chat_active = True 
        
        current_h = self.page.height if self.page.height else 800
        self.sheet_content.height = current_h - 10 
        
        chat_view = ChatContent(
            self.page, 
            self.user, 
            target_profile, 
            on_back=lambda: self.open_profile(target_profile)
        )
        self.sheet_content.content = chat_view
        self.sheet_content.update()
        
        if hasattr(chat_view, "did_mount"):
            chat_view.did_mount()

    async def _update_user_role(self, profile, is_admin):
        new_role = "ADMIN" if is_admin else "USER"
        success = await AuthService.update_profile_general(profile["id"], {"role": new_role})
        if success:
            profile["role"] = new_role 
            action = "promovido a Administrador" if is_admin else "rebaixado a Usuário"
            self.page.snack_bar = ft.SnackBar(ft.Text(f"{profile['name']} foi {action}!"), bgcolor=ft.Colors.GREEN)
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Erro ao atualizar permissão."), bgcolor=ft.Colors.RED)
        self.page.snack_bar.open = True
        self.page.update()

    async def _build_flight_status_widget(self, profile):
        try:
            flights = await FlightService.get_flights()
            now = datetime.now()
            current_year = now.year
            active_segment = None
            status_type = "" 

            for f in flights:
                if str(f.get("user_id")) != str(profile["id"]): continue
                segments = f.get("segments", [])
                for seg in segments:
                    try:
                        date_str = seg.get("date", "")
                        time_str = seg.get("time", "")
                        if len(date_str) == 5: date_str = f"{date_str}/{current_year}"
                        arr_time_str = seg.get("arr_time", time_str)
                        if not date_str or not time_str: continue

                        dep_dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
                        arr_dt = datetime.strptime(f"{date_str} {arr_time_str}", "%d/%m/%Y %H:%M")
                        if arr_dt < dep_dt: arr_dt += timedelta(days=1)

                        if (dep_dt - timedelta(hours=4)) <= now < dep_dt:
                            active_segment = seg; status_type = "boarding"; break
                        elif dep_dt <= now <= arr_dt:
                            active_segment = seg; status_type = "flying"; break
                        elif arr_dt < now <= (arr_dt + timedelta(hours=4)):
                            active_segment = seg; status_type = "landed"; break
                    except: continue
                if active_segment: break

            if not active_segment: return ft.Container()

            color, icon, subtext = ft.Colors.BLUE_700, ft.Icons.AIRPLANE_TICKET, ""
            title_text = f"Voo {active_segment.get('code', '???')}"

            if status_type == "boarding":
                color = ft.Colors.ORANGE_800
                icon = ft.Icons.DEPARTURE_BOARD
                minutes = int((dep_dt - now).total_seconds() / 60)
                subtext = f"Embarque em {minutes} min • Portão {active_segment.get('gate','?') or '?'}"
            elif status_type == "flying":
                color = ft.Colors.INDIGO_900
                icon = ft.Icons.AIRPLANEMODE_ACTIVE
                subtext = f"Rumo a {active_segment.get('dest','Destino')}"
            elif status_type == "landed":
                color = ft.Colors.GREEN_800
                icon = ft.Icons.FLIGHT_LAND
                subtext = f"Chegou em {active_segment.get('dest','Destino')}"

            return ft.Container(
                bgcolor=color, border_radius=10, padding=12, margin=ft.margin.only(bottom=15),
                content=ft.Row([
                    ft.Container(padding=10, bgcolor=ft.Colors.BLACK26, border_radius=50, content=ft.Icon(icon, color="white", size=24)),
                    ft.Column([
                        ft.Text(title_text, weight="bold", size=16, color="white"),
                        ft.Text(subtext, size=12, color="white70")
                    ], spacing=2)
                ], alignment=ft.MainAxisAlignment.START)
            )
        except: return ft.Container()

    def _build_action_tile(self, text, icon, color, on_click, disabled=False, badge_count=0):
        base_btn = ft.Container(
            bgcolor=color, 
            border_radius=12, 
            padding=10,
            expand=True,
            ink=True, 
            on_click=on_click, 
            opacity=0.5 if disabled else 1,
            content=ft.Row([
                ft.Icon(icon, color="white"),
                ft.Text(text, weight="bold", color="white")
            ], alignment=ft.MainAxisAlignment.CENTER) 
        )
        
        if badge_count > 0:
            return ft.Stack([
                base_btn,
                ft.Container(
                    content=ft.Text(str(badge_count), color="white", size=10, weight="bold"),
                    bgcolor=ft.Colors.RED,
                    width=20, height=20, border_radius=10,
                    alignment=ft.Alignment(0, 0),
                    right=0, top=0,
                    border=ft.border.all(2, ft.Colors.GREY_900)
                )
            ])
        else:
            return base_btn

    def _navigate_to_view(self, profile, view_type):
        content = None
        if view_type == "medical": content = self._build_medical_detail(profile)
        elif view_type == "docs": content = self._build_docs_detail(profile)
        elif view_type == "contact": content = self._build_contact_detail(profile)
        if content: self.sheet_content.content = content; self.sheet_content.update()

    def _build_medical_detail(self, profile):
        is_me = str(profile["id"]) == str(self.user["id"])
        privacy_open = profile.get("privacy", {}).get("medical", False)
        if not is_me and not privacy_open: return self._build_restricted_view(profile, "Ficha Médica")
        med = profile.get("medical", {})
        return ft.Container(
            padding=20, height=600,
            content=ft.Column([
                self._build_back_header("Ficha Médica", profile),
                ft.Divider(),
                ft.ListView(expand=True, spacing=15, controls=[
                    self._info_card("Tipo Sanguíneo / Doador", f"{med.get('blood_type', '?')}  |  Doador: {'Sim' if med.get('donor') else 'Não'}", ft.Icons.BLOODTYPE, ft.Colors.RED),
                    self._info_card("Alergias", med.get("allergies", "Nenhuma"), ft.Icons.WARNING, ft.Colors.ORANGE),
                    self._info_card("Medicamentos", med.get("medications", "Nenhum"), ft.Icons.MEDICATION, ft.Colors.BLUE),
                    self._info_card("Vacinas", med.get("vaccines", "Em dia"), ft.Icons.VACCINES, ft.Colors.TEAL),
                    self._info_card("Plano de Saúde", f"{med.get('health_plan', {}).get('name', '--')} \nNum: {med.get('health_plan', {}).get('number', '--')}", ft.Icons.LOCAL_HOSPITAL, ft.Colors.CYAN),
                    self._info_card("Médico", f"{med.get('doctor', {}).get('name', '--')} - {med.get('doctor', {}).get('phone', '--')}", ft.Icons.PERSON, ft.Colors.PURPLE),
                    self._info_card("Notas", med.get("notes", ""), ft.Icons.NOTE, ft.Colors.GREY)
                ])
            ])
        )

    def _build_docs_detail(self, profile):
        is_me = str(profile["id"]) == str(self.user["id"])
        privacy_open = profile.get("privacy", {}).get("passport", False) 
        if not is_me and not privacy_open: return self._build_restricted_view(profile, "Documentos")
        return ft.Container(
            padding=20, height=600,
            content=ft.Column([
                self._build_back_header("Documentos Pessoais", profile),
                ft.Divider(),
                ft.ListView(expand=True, spacing=10, controls=[
                    self._simple_tile("Passaporte", profile.get("passport", "Não informado"), ft.Icons.BOOK),
                    self._simple_tile("CPF", profile.get("cpf", "Não informado"), ft.Icons.FINGERPRINT),
                    self._simple_tile("RG", profile.get("rg", "Não informado"), ft.Icons.BADGE),
                ])
            ])
        )

    def _build_contact_detail(self, profile):
        ct = profile.get("contact", {})
        return ft.Container(
            padding=20, height=600,
            content=ft.Column([
                self._build_back_header("Contatos", profile),
                ft.Divider(),
                ft.ListView(expand=True, spacing=10, controls=[
                    self._simple_tile("Telefone", ct.get("phone", "--"), ft.Icons.PHONE),
                    self._simple_tile("E-mail", ct.get("email", "--"), ft.Icons.EMAIL),
                    ft.Divider(),
                    ft.Text("EMERGÊNCIA", weight="bold", color=ft.Colors.RED),
                    self._simple_tile("Nome Contato", ct.get("emergency_name", "--"), ft.Icons.CONTACT_PHONE, color=ft.Colors.RED),
                    self._simple_tile("Tel. Emergência", ct.get("emergency_phone", "--"), ft.Icons.PHONE_IN_TALK, color=ft.Colors.RED),
                ])
            ])
        )

    def _build_restricted_view(self, profile, title):
        return ft.Container(
            padding=20, height=400,
            content=ft.Column([
                self._build_back_header(title, profile),
                ft.Divider(),
                ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=ft.Column([
                    ft.Icon(ft.Icons.LOCK, size=50, color=ft.Colors.GREY_700),
                    ft.Text("Informação Privada", size=18, weight="bold", color=ft.Colors.GREY_500),
                    ft.Text(f"{profile['name']} optou por não compartilhar.", color=ft.Colors.GREY_600)
                ], horizontal_alignment="center", alignment=ft.MainAxisAlignment.CENTER))
            ])
        )

    def _build_back_header(self, title, profile):
        return ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.open_profile(profile)),
            ft.Text(title, size=20, weight="bold"),
        ])

    def _info_card(self, label, value, icon, color):
        if not value: value = "--"
        return ft.Container(
            padding=10, bgcolor=ft.Colors.BLACK12, border_radius=8,
            content=ft.Row([
                ft.Container(content=ft.Icon(icon, color=color), padding=10, bgcolor=ft.Colors.BLACK26, border_radius=8),
                ft.Column([
                    ft.Text(label, size=12, color=ft.Colors.GREY_400),
                    ft.Text(str(value), size=14, weight="bold", selectable=True)
                ], spacing=2, expand=True)
            ])
        )

    def _simple_tile(self, label, value, icon, color=ft.Colors.CYAN):
        return ft.ListTile(
            leading=ft.Icon(icon, color=color),
            title=ft.Text(label, size=12, color=ft.Colors.GREY_400),
            subtitle=ft.Text(value, size=16, weight="bold"),
        )