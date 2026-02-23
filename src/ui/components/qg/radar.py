import flet as ft
import time
import asyncio
from src.logic.auth_service import AuthService

class QGRadar(ft.Column):
    def __init__(self, page: ft.Page, user, on_click_profile):
        super().__init__(spacing=5)
        self.page_ref = page
        self.user = user
        self.on_click_profile = on_click_profile
        self.heartbeat_running = False
        
        self.radar_carousel = ft.Row(scroll=ft.ScrollMode.HIDDEN, spacing=15)
        
        self.controls = [
            ft.Text("Membros da Viagem", weight="bold", size=16),
            ft.Container(
                content=self.radar_carousel,
                height=110,
                padding=ft.padding.symmetric(vertical=10)
            )
        ]

    def start_loop(self):
        self.heartbeat_running = True
        self.page_ref.run_task(self._radar_loop)

    def stop_loop(self):
        self.heartbeat_running = False

    async def _radar_loop(self):
        while self.heartbeat_running:
            try:
                await AuthService.update_presence(self.user["id"], is_heartbeat=True)
                await self._load_profiles_radar()
            except Exception as e:
                print(f"Erro no Radar: {e}")
            await asyncio.sleep(60)

    async def _load_profiles_radar(self):
        profiles = await AuthService.get_profiles()
        profiles.sort(key=lambda p: str(p["id"]) == str(self.user["id"]), reverse=True)

        self.radar_carousel.controls = []
        now = time.time()
        
        for p in profiles:
            initials = p["name"][:2].upper()
            role = p.get("role", "USER")
            is_me = str(p["id"]) == str(self.user["id"])
            
            size, font_size = (75, 24) if is_me else (60, 18)
            border_color = ft.Colors.CYAN_300 if is_me else (ft.Colors.ORANGE if role == "ADMIN" else ft.Colors.CYAN_800)
            border_width = 3 if is_me else 2
            box_shadow = ft.BoxShadow(blur_radius=15, color=ft.Colors.CYAN_900) if is_me else None

            last_seen = p.get("last_seen", 0)
            is_online = (now - last_seen) < 300 
            status_color = ft.Colors.GREEN if is_online else ft.Colors.GREY_600
            if is_me: status_color = ft.Colors.GREEN

            avatar = ft.Stack([
                ft.Container(
                    width=size, height=size, border_radius=size/2,
                    bgcolor=ft.Colors.GREY_800,
                    border=ft.border.all(border_width, border_color),
                    shadow=box_shadow,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(initials, size=font_size, weight="bold", color=ft.Colors.WHITE)
                ),
                ft.Container(
                    width=16, height=16, border_radius=8, bgcolor=status_color,
                    border=ft.border.all(2, ft.Colors.BLACK),
                    right=0, bottom=2 if is_me else 0
                )
            ])
            
            item = ft.Container(
                content=ft.Column([
                    avatar,
                    ft.Text(p["name"].split()[0], size=11, weight="bold" if is_me else "normal", color=ft.Colors.CYAN_200 if is_me else ft.Colors.WHITE, width=80, text_align="center", no_wrap=True)
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                on_click=lambda e, prof=p: self.on_click_profile(prof)
            )
            self.radar_carousel.controls.append(item)
        self.update()