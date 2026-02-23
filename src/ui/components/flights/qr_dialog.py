import flet as ft
import urllib.parse

class QRDialogManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.qr_img = ft.Image(src="", fit="contain", expand=True)
        self.qr_label = ft.Text("", size=18, weight="bold", text_align="center", color=ft.Colors.BLACK)
        
        self.dialog = ft.AlertDialog(
            bgcolor=ft.Colors.WHITE, inset_padding=10,
            content=ft.Column([
                ft.Text("CARTÃO DE EMBARQUE", weight="bold", size=24, text_align="center", color=ft.Colors.BLACK),
                ft.Container(content=self.qr_img, expand=True, alignment=ft.Alignment(0,0)),
                self.qr_label,
                ft.Text("Aumente o brilho do celular", color=ft.Colors.GREY_700, size=14, text_align="center")
            ], alignment="center", horizontal_alignment="center"),
            actions=[ft.Container(ft.ElevatedButton("FECHAR", on_click=self._close, bgcolor=ft.Colors.BLACK, color=ft.Colors.WHITE, height=50, width=150), alignment=ft.Alignment(0,0), padding=10)]
        )

    def open(self, segment, user_name):
        official = segment.get("raw_code")
        if official:
            content = official
            self.qr_label.value = "CÓDIGO OFICIAL"
            self.qr_label.color = ft.Colors.GREEN_700
        else:
            content = f"PNR:{segment.get('code')}|SEAT:{segment.get('seat')}|PAX:{user_name}"
            self.qr_label.value = "QR GENÉRICO (TESTE)"
            self.qr_label.color = ft.Colors.ORANGE_800

        self.qr_img.src = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(content)}"
        if self.dialog not in self.page.overlay: self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _close(self, e):
        self.dialog.open = False
        self.page.update()