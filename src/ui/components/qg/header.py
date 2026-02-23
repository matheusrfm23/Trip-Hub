import flet as ft

class QGHeader(ft.Row):
    def __init__(self, user, on_click_profile):
        super().__init__(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        self.user = user
        self.on_click_profile = on_click_profile
        
        user_name = self.user["name"].split()[0]
        avatar_initials = self.user["name"][:2].upper()

        self.controls = [
            ft.Column([
                ft.Text(f"Olá, {user_name}!", size=26, weight="bold"),
                ft.Text("Painel da Viagem", size=14, color=ft.Colors.GREY)
            ], spacing=2),
            ft.Container(
                content=ft.Text(avatar_initials, weight="bold", color=ft.Colors.WHITE, size=20),
                bgcolor=ft.Colors.CYAN_900,
                width=55, height=55, border_radius=30, alignment=ft.Alignment(0, 0),
                border=ft.border.all(2, ft.Colors.CYAN_400),
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.CYAN_900),
                on_click=lambda e: self.on_click_profile(self.user)
            )
        ]