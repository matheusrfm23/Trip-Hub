import flet as ft
from src.logic.notification_service import NotificationService
from src.core.profiler import track_execution

class QGHeader(ft.Row):
    def __init__(self, page: ft.Page, user, on_click_profile):
        super().__init__(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        self.page_ref = page  # Renomeado para evitar conflito com propriedade page
        self.user = user
        self.on_click_profile = on_click_profile
        
        user_name = self.user["name"].split()[0]
        avatar_initials = self.user["name"][:2].upper()

        # --- NOTIFICAÇÕES ---
        self.notifications_dialog = ft.AlertDialog(
            title=ft.Text("Notificações", weight="bold"),
            content=ft.Container(
                width=400, height=400,
                content=ft.Column(scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Marcar todas como lidas", on_click=self._mark_all_read),
                ft.TextButton("Fechar", on_click=self._close_notifications)
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.notification_badge = ft.Container(
            content=ft.Text("0", color=ft.Colors.WHITE, size=10, weight="bold"),
            bgcolor=ft.Colors.RED,
            width=16, height=16, border_radius=8,
            alignment=ft.Alignment(0, 0),
            visible=False,
            right=5, top=5
        )

        self.btn_notifications = ft.Stack([
            ft.IconButton(
                ft.Icons.NOTIFICATIONS_OUTLINED,
                icon_color=ft.Colors.WHITE,
                on_click=self._open_notifications,
                tooltip="Notificações"
            ),
            self.notification_badge
        ])

        # --- PROFILE AVATAR ---
        self.avatar = ft.Container(
            content=ft.Text(avatar_initials, weight="bold", color=ft.Colors.WHITE, size=20),
            bgcolor=ft.Colors.CYAN_900,
            width=50, height=50, border_radius=25, alignment=ft.Alignment(0, 0),
            border=ft.border.all(2, ft.Colors.CYAN_400),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.CYAN_900),
            on_click=lambda e: self.on_click_profile(self.user),
            ink=True
        )

        self.controls = [
            ft.Column([
                ft.Text(f"Olá, {user_name}!", size=24, weight="bold"),
                ft.Text("Painel da Viagem", size=12, color=ft.Colors.GREY)
            ], spacing=0),

            ft.Row([
                self.btn_notifications,
                self.avatar
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        ]

    def did_mount(self):
        # Carrega contagem inicial
        self.page_ref.run_task(self._update_badge)

    async def _update_badge(self):
        try:
            count = await NotificationService.get_unread_count(self.user["id"])
            if count > 0:
                self.notification_badge.content.value = str(count) if count < 99 else "99+"
                self.notification_badge.visible = True
            else:
                self.notification_badge.visible = False
            self.notification_badge.update()
        except Exception as e:
            print(f"Erro badge: {e}")

    async def _open_notifications(self, e):
        # [CORREÇÃO] Garante overlay e abre imediatamente (Padrão Clássico)
        if self.notifications_dialog not in self.page_ref.overlay:
            self.page_ref.overlay.append(self.notifications_dialog)
        self.notifications_dialog.open = True
        self.page_ref.update()

        # Carrega lista em background
        content_col = self.notifications_dialog.content.content
        content_col.controls = [ft.ProgressRing()]
        # Atualiza o dialog novamente para mostrar o loading
        self.notifications_dialog.update()

        # Busca dados
        notifs = await NotificationService.get_notifications(self.user["id"])

        items = []
        if not notifs:
            items.append(ft.Text("Nenhuma notificação.", italic=True, color=ft.Colors.GREY))
        else:
            for n in notifs:
                is_read = str(self.user["id"]) in n.get("read_by", [])
                icon_color = ft.Colors.GREY if is_read else ft.Colors.CYAN
                items.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=icon_color),
                        title=ft.Text(n.get("title", "Aviso"), weight="bold" if not is_read else "normal"),
                        subtitle=ft.Text(n.get("message", ""), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        trailing=ft.Text(n.get("timestamp", "")[:5], size=10),
                        on_click=lambda e, nid=n["id"]: self.page_ref.run_task(self._read_notification, nid)
                    )
                )

        content_col.controls = items
        self.notifications_dialog.update()

        # Atualiza badge ao abrir (opcional, ou manter até ler)
        await self._update_badge()

    async def _read_notification(self, notif_id):
        await NotificationService.mark_as_read(notif_id, self.user["id"])
        # Recarrega lista e badge
        # Fechamos e reabrimos ou apenas atualizamos? Melhor atualizar a lista.
        # Por simplicidade, fechamos o dialog para o usuário ver que leu, ou atualizamos visualmente.
        # Vamos apenas atualizar o badge por enquanto e fechar o dialog se quiser.
        # Mas o usuário pode querer ler várias.
        # Idealmente: Atualizar a UI do item para "lido".
        # Simplificação: Fecha e atualiza badge.
        self.notifications_dialog.open = False
        self.page_ref.update()
        await self._update_badge()

    async def _mark_all_read(self, e):
        await NotificationService.mark_all_read(self.user["id"])
        self.notifications_dialog.open = False
        self.page_ref.update()
        await self._update_badge()

    def _close_notifications(self, e):
        self.notifications_dialog.open = False
        self.page_ref.update()
