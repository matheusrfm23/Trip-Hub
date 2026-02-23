# ARQUIVO: src/ui/views/dashboard_view.py
import flet as ft
from src.ui.components.qg.qg_content import QGContent
from src.ui.components.traveler_content import TravelerContent
from src.ui.components.utilities_content import UtilitiesContent
from src.ui.components.flights_content import FlightsContent
from src.ui.components.medical_content import MedicalContent
from src.ui.components.finance_content import FinanceContent
from src.ui.components.leisure.game_hub import GameHub
from src.ui.components.utilities.quick_access import QuickAccessButton

from src.logic.finance_service import FinanceService
from src.logic.auth_service import AuthService
from src.logic.notification_service import NotificationService 

class DashboardView(ft.View):
    def __init__(self, page: ft.Page):
        super().__init__(route="/dashboard")
        self.main_page = page
        self.bgcolor = ft.Colors.BLACK
        self.padding = 0 
        self.user = self.main_page.user_profile
        
        user_name = self.user.get("name", "Viajante").split()[0]

        # --- SINO COM BADGE ---
        self.badge_count = ft.Text("0", size=10, color=ft.Colors.WHITE, weight="bold")
        self.badge_container = ft.Container(
            content=self.badge_count,
            width=16, height=16,
            bgcolor=ft.Colors.RED,
            border_radius=8,
            alignment=ft.Alignment(0, 0),
            visible=False 
        )
        
        self.notification_bell = ft.Stack(
            controls=[
                ft.IconButton(
                    ft.Icons.NOTIFICATIONS, 
                    tooltip="Central de Avisos", 
                    on_click=self._open_notifications
                ),
                ft.Container(
                    content=self.badge_container,
                    right=5, top=5 
                )
            ]
        )

        # --- APPBAR ---
        self.appbar = ft.AppBar(
            title=ft.Text("TripHub", weight="bold", font_family="Verdana"),
            center_title=True,
            bgcolor=ft.Colors.BLACK,
            leading=ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                tooltip="Menu Principal",
                items=[
                    ft.PopupMenuItem(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PERSON, color=ft.Colors.CYAN),
                            ft.Text("Perfil", color=ft.Colors.WHITE),
                            ft.Text(f"({user_name})", color=ft.Colors.CYAN_200, weight="bold")
                        ]),
                        on_click=self._show_traveler_profile
                    ),
                    ft.PopupMenuItem(), 
                    self._build_menu_item("Meus Voos", ft.Icons.AIRPLANE_TICKET, self._show_flights),
                    self._build_menu_item("Ficha Médica", ft.Icons.MEDICAL_SERVICES, self._show_medical),
                    ft.PopupMenuItem(), 
                    # [CORREÇÃO AQUI] Mudamos a rota para /logout
                    self._build_menu_item("Sair", ft.Icons.EXIT_TO_APP, lambda _: self.main_page.go("/logout"), color=ft.Colors.RED_400),
                ]
            ),
            actions=[
                ft.Container(content=self.notification_bell, padding=ft.padding.only(right=10))
            ]
        )
        
        self.body_container = ft.Container(expand=True)

        self.navigation_bar = ft.NavigationBar(
            bgcolor=ft.Colors.GREY_900,
            selected_index=0,
            indicator_color=ft.Colors.CYAN_900,
            on_change=self._nav_change,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="QG"),
                ft.NavigationBarDestination(icon=ft.Icons.HANDYMAN, label="Utilidades"), 
                ft.NavigationBarDestination(icon=ft.Icons.ATTACH_MONEY, label="Finanças"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_ESPORTS, label="Lazer"),
            ]
        )

        self.controls = [self.body_container]
        self.body_container.content = QGContent(self.main_page, self._go_to_country)
        
        self._setup_notification_dialog()

    def did_mount(self):
        self.main_page.run_task(self._update_badge)
        if self.main_page.user_profile.get("pin") == "0000":
            self._show_security_alert()

    async def _update_badge(self):
        try:
            count = await NotificationService.get_unread_count(self.user["id"])
            if count > 0:
                self.badge_count.value = str(count) if count < 99 else "99+"
                self.badge_container.visible = True
            else:
                self.badge_container.visible = False
            self.badge_container.update()
        except: pass

    # --- CENTRAL DE NOTIFICAÇÕES ---
    def _setup_notification_dialog(self):
        self.notif_list = ft.Column(
            scroll=ft.ScrollMode.AUTO, 
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH 
        )
        
        self.msg_target = ft.Dropdown(label="Para quem?", options=[], value="ALL")
        self.msg_title = ft.TextField(label="Assunto", hint_text="Ex: Jantar hoje")
        self.msg_body = ft.TextField(label="Mensagem", multiline=True, min_lines=3)
        self.send_status = ft.Text("", size=12)

        self.current_notif_tab = "inbox"
        self.nav_buttons_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
        self._update_nav_buttons()

        self.tab_content_area = ft.Container(
            height=350,
            width=400, 
            padding=10,
            content=self.notif_list,
            border=ft.border.all(1, ft.Colors.WHITE10),
            border_radius=8
        )
        
        self.notif_dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color=ft.Colors.CYAN), 
                ft.Text("Central de Avisos")
            ]),
            content=ft.Container(
                width=450, 
                content=ft.Column([
                    self.nav_buttons_row,
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    self.tab_content_area
                ])
            ),
            actions=[
                ft.TextButton("Marcar todas lidas", on_click=self._mark_all_read),
                ft.TextButton("Fechar", on_click=self._close_notification_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _update_nav_buttons(self):
        inbox_selected = self.current_notif_tab == "inbox"
        
        btn_inbox = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INBOX, size=16, color=ft.Colors.WHITE if inbox_selected else ft.Colors.GREY),
                ft.Text("Entrada", color=ft.Colors.WHITE if inbox_selected else ft.Colors.GREY)
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
            bgcolor=ft.Colors.CYAN_900 if inbox_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            on_click=lambda e: self._switch_notif_tab("inbox"),
            ink=True,
            expand=True 
        )
        
        btn_compose = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SEND, size=16, color=ft.Colors.WHITE if not inbox_selected else ft.Colors.GREY),
                ft.Text("Novo Aviso", color=ft.Colors.WHITE if not inbox_selected else ft.Colors.GREY)
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
            bgcolor=ft.Colors.CYAN_900 if not inbox_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            on_click=lambda e: self._switch_notif_tab("compose"),
            ink=True,
            expand=True
        )
        
        buttons = [btn_inbox]
        if self.user.get("role") == "ADMIN":
            buttons.append(btn_compose)
            
        self.nav_buttons_row.controls = buttons

    def _switch_notif_tab(self, tab_name):
        self.current_notif_tab = tab_name
        self._update_nav_buttons()
        self.nav_buttons_row.update()
        
        if tab_name == "inbox":
            self.tab_content_area.content = self.notif_list
            self.main_page.run_task(self._fetch_notifications)
        else:
            admin_tools = ft.Column([
                ft.Divider(color=ft.Colors.GREY_800),
                ft.Text("Zona de Perigo (Admin)", size=12, color=ft.Colors.RED),
                ft.ElevatedButton(
                    "LIMPAR TODAS AS NOTIFICAÇÕES", 
                    icon=ft.Icons.DELETE_FOREVER, 
                    bgcolor=ft.Colors.RED_900, 
                    color=ft.Colors.WHITE,
                    on_click=self._clear_all_notifications
                )
            ]) if self.user.get("role") == "ADMIN" else ft.Container()

            self.tab_content_area.content = ft.Column([
                ft.Text("Enviar Comunicado", weight="bold", color=ft.Colors.ORANGE, size=16),
                self.msg_target,
                self.msg_title,
                self.msg_body,
                self.send_status,
                ft.Container(height=5),
                ft.ElevatedButton("ENVIAR AGORA", icon=ft.Icons.SEND, bgcolor=ft.Colors.CYAN, color=ft.Colors.BLACK, on_click=self._send_broadcast, width=400),
                admin_tools
            ], spacing=10, scroll=ft.ScrollMode.AUTO)
            self.main_page.run_task(self._load_users_for_dropdown)
            
        self.tab_content_area.update()

    def _open_notifications(self, e):
        self.current_notif_tab = "inbox"
        self._update_nav_buttons()
        self.tab_content_area.content = self.notif_list
        self.main_page.run_task(self._fetch_notifications)
        
        if self.notif_dialog not in self.main_page.overlay:
            self.main_page.overlay.append(self.notif_dialog)
        self.notif_dialog.open = True
        self.main_page.update()

    def _close_notification_dialog(self, e):
        self.notif_dialog.open = False
        self.main_page.overlay.clear() 
        self.main_page.update()

    async def _clear_all_notifications(self, e):
        await NotificationService.clear_all()
        self.send_status.value = "Todas as notificações foram apagadas!"
        self.send_status.color = ft.Colors.RED
        self.send_status.update()
        await self._update_badge()

    async def _load_users_for_dropdown(self):
        profiles = await AuthService.get_profiles()
        opts = [ft.dropdown.Option("ALL", "📢 TODOS DO GRUPO")]
        for p in profiles:
            if str(p["id"]) != str(self.user["id"]):
                opts.append(ft.dropdown.Option(str(p["id"]), p["name"]))
        self.msg_target.options = opts
        self.msg_target.update()

    async def _send_broadcast(self, e):
        if not self.msg_title.value or not self.msg_body.value:
            self.send_status.value = "Preencha todos os campos!"
            self.send_status.color = ft.Colors.RED
            self.send_status.update()
            return

        success = await NotificationService.send_notification(
            sender_name=self.user["name"],
            target_id=self.msg_target.value,
            title=self.msg_title.value,
            message=self.msg_body.value
        )

        if success:
            self.msg_title.value = ""
            self.msg_body.value = ""
            self.send_status.value = "Mensagem enviada com sucesso!"
            self.send_status.color = ft.Colors.GREEN
            self.notif_dialog.update()
        else:
            self.send_status.value = "Erro ao enviar."
            self.send_status.update()

    async def _mark_all_read(self, e):
        await NotificationService.mark_all_read(self.user["id"])
        await self._fetch_notifications() 
        await self._update_badge()

    async def _fetch_notifications(self):
        fin_notifs = await FinanceService.get_notifications(self.user["id"])
        gen_notifs = await NotificationService.get_notifications(self.user["id"])
        
        self.notif_list.controls = []
        
        if not fin_notifs and not gen_notifs:
            self.notif_list.controls.append(
                ft.Container(
                    padding=40, 
                    alignment=ft.Alignment(0,0),
                    content=ft.Column([
                        ft.Icon(ft.Icons.NOTIFICATIONS_OFF, size=50, color=ft.Colors.GREY_800),
                        ft.Text("Nenhum aviso por enquanto.", color=ft.Colors.GREY, size=16)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )
        else:
            for n in fin_notifs:
                item = ft.Container(
                    bgcolor=ft.Colors.RED_900, padding=15, border_radius=8,
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.WHITE, size=30),
                        ft.Column([
                            ft.Text("Contestação de Dívida", weight="bold", size=14, color=ft.Colors.WHITE),
                            ft.Text(f"{n['description']} - {n['amount_fmt']}", size=12, color=ft.Colors.WHITE70)
                        ], expand=True)
                    ])
                )
                self.notif_list.controls.append(item)

            for n in gen_notifs:
                is_read = str(self.user["id"]) in n.get("read_by", [])
                
                card_color = ft.Colors.GREY_900 if is_read else ft.Colors.BLUE_GREY_900
                text_color = ft.Colors.GREY_400 if is_read else ft.Colors.WHITE
                title_color = ft.Colors.WHITE if not is_read else ft.Colors.GREY
                border_color = ft.Colors.TRANSPARENT if is_read else ft.Colors.CYAN_700
                
                is_broadcast = n["target_id"] == "ALL"
                icon = ft.Icons.CAMPAIGN if is_broadcast else ft.Icons.MAIL
                icon_color = ft.Colors.ORANGE if is_broadcast else ft.Colors.CYAN
                
                item = ft.Container(
                    bgcolor=card_color, 
                    padding=15, 
                    border_radius=8,
                    border=ft.border.all(1, border_color),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(icon, color=icon_color, size=24),
                            ft.Text(n["title"], weight="bold", size=16, expand=True, color=title_color),
                            ft.Text(n["timestamp"], size=12, color=ft.Colors.GREY)
                        ]),
                        ft.Text(n["message"], size=14, color=text_color, selectable=True),
                        ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                        ft.Row([
                            ft.Text(f"Enviado por: {n['sender']}", size=12, color=ft.Colors.GREY_500, italic=True),
                            ft.Container(expand=True),
                            ft.IconButton(
                                ft.Icons.CHECK_CIRCLE_OUTLINE if not is_read else ft.Icons.CHECK_CIRCLE,
                                icon_size=24,
                                icon_color=ft.Colors.GREEN if is_read else ft.Colors.GREY_700,
                                tooltip="Marcar como lida",
                                disabled=is_read,
                                on_click=lambda e, nid=n["id"]: self.main_page.run_task(self._mark_single_read, nid)
                            )
                        ])
                    ])
                )
                self.notif_list.controls.append(item)
        
        self.notif_list.update()
        await self._update_badge()

    async def _mark_single_read(self, notif_id):
        await NotificationService.mark_as_read(notif_id, self.user["id"])
        await self._fetch_notifications()

    # --- Outras Funções ---
    def _show_security_alert(self):
        def go_to_profile(e):
            self.security_dialog.open = False
            self.main_page.update()
            self._show_traveler_profile(None)

        self.security_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ Segurança"),
            content=ft.Text("Sua senha ainda é a padrão (0000)."),
            actions=[
                ft.TextButton("Depois", on_click=lambda e: setattr(self.security_dialog, 'open', False) or self.main_page.update()),
                ft.ElevatedButton("Trocar Agora", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, on_click=go_to_profile)
            ]
        )
        self.main_page.dialog = self.security_dialog
        self.security_dialog.open = True
        self.main_page.update()

    def _nav_change(self, e):
        idx = e.control.selected_index
        
        # --- LÓGICA DO BOTÃO DE ADUANA (Acesso Rápido) ---
        if idx == 1:
            self.floating_action_button = QuickAccessButton(self.main_page, user_profile=self.user)
        else:
            self.floating_action_button = None
        self.update() 
        # --------------------------------------------------

        if idx == 0:
            content = QGContent(self.main_page, self._go_to_country)
            if hasattr(content, 'did_mount'): content.did_mount()
            self.body_container.content = content
        elif idx == 1:
            self.body_container.content = UtilitiesContent(self.main_page)
        elif idx == 2:
            self.body_container.content = FinanceContent(self.main_page)
        elif idx == 3:
            # Integração corrigida com GameHub
            self.body_container.content = GameHub(self.main_page)
        
        self.update()

    def _show_traveler_profile(self, e):
        self.body_container.content = TravelerContent(self.main_page)
        self.update()

    def _show_flights(self, e):
        self.body_container.content = FlightsContent(self.main_page)
        self.update()

    def _show_medical(self, e):
        self.body_container.content = MedicalContent(self.main_page)
        self.update()

    def _go_to_country(self, name, code, color):
        self.main_page.go(f"/country/{code}")

    def _build_menu_item(self, text, icon, action, color=ft.Colors.WHITE):
        return ft.PopupMenuItem(
            content=ft.Row([ft.Icon(icon, color=color), ft.Text(text, color=color)]),
            on_click=action
        )