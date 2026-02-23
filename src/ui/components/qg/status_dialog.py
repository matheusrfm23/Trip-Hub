import flet as ft
import urllib.parse
from src.logic.auth_service import AuthService

class StatusDialogManager:
    def __init__(self, page: ft.Page, user, on_update_callback):
        self.page = page
        self.user = user
        self.on_update_callback = on_update_callback # Chama o Radar Refresh
        
        self.tf_location = ft.TextField(label="Onde estou?", hint_text="Ex: Hotel, Restaurante...", prefix_icon=ft.Icons.PIN_DROP, expand=True)
        self.btn_gps = ft.IconButton(icon=ft.Icons.MY_LOCATION, icon_color=ft.Colors.CYAN_400, tooltip="GPS (HTTPS)", on_click=self._simulate_gps_error)
        self.dd_status = ft.Dropdown(label="O que estou fazendo?", options=[ft.dropdown.Option("Disponível"), ft.dropdown.Option("Ocupado"), ft.dropdown.Option("Comendo"), ft.dropdown.Option("Em Compras"), ft.dropdown.Option("Dormindo")], value="Disponível")
        self.gps_status_text = ft.Text("", size=10, italic=True, color=ft.Colors.GREY)

        self.dialog = ft.AlertDialog(
            title=ft.Text("Atualizar Radar"),
            content=ft.Container(height=180, content=ft.Column([ft.Row([self.tf_location, self.btn_gps]), self.gps_status_text, self.dd_status])),
            actions=[ft.TextButton("Cancelar", on_click=self._close), ft.ElevatedButton("ATUALIZAR", bgcolor=ft.Colors.CYAN, color=ft.Colors.WHITE, on_click=self._save_status)]
        )

    def open_for_me(self, profile):
        self.tf_location.value = profile.get("last_location", "")
        self.dd_status.value = profile.get("status_msg", "Disponível")
        self.gps_status_text.value = "" 
        if self.dialog not in self.page.overlay: self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def handle_click(self, profile):
        is_me = str(profile["id"]) == str(self.user["id"])
        if is_me:
            self.open_for_me(profile)
        else:
            location = profile.get("last_location", "")
            if location and len(location) > 3: 
                encoded_loc = urllib.parse.quote(location)
                self.page.launch_url(f"https://www.google.com/maps/search/?api=1&query={encoded_loc}")
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Localização não definida."), bgcolor=ft.Colors.GREY_800)
                self.page.snack_bar.open = True
                self.page.update()

    async def _simulate_gps_error(self, e):
        self.gps_status_text.value = "⚠️ GPS bloqueado em Rede Local (HTTP)."
        self.gps_status_text.color = ft.Colors.ORANGE
        self.page.snack_bar = ft.SnackBar(ft.Text("Por segurança, digite o local manualmente."), bgcolor=ft.Colors.ORANGE)
        self.page.snack_bar.open = True
        await self.tf_location.focus()
        self.dialog.update()
        self.page.update()

    def _close(self, e): 
        self.dialog.open = False
        self.page.update()

    async def _save_status(self, e):
        await AuthService.update_presence(self.user["id"], location=self.tf_location.value, status_msg=self.dd_status.value)
        self.dialog.open = False
        self.page.snack_bar = ft.SnackBar(ft.Text("Radar atualizado!"), bgcolor=ft.Colors.GREEN)
        self.page.snack_bar.open = True
        self.page.update()
        if self.on_update_callback:
            await self.on_update_callback()