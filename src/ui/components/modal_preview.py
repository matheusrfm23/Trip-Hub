import flet as ft

from src.core.utils import get_file_details


class ModalPreview:
    def __init__(self, page: ft.Page):
        self.page = page
        self.files_list = []
        self.current_index = 0
        self.visible = False

        # Elementos UI
        self.preview_img = ft.Image(src="", fit="contain")
        self.preview_icn = ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=100)
        self.txt_info = ft.Text("-", size=14, color="white", text_align="center")
        
        # Botões
        self.btn_download = ft.IconButton(
            icon=ft.Icons.DOWNLOAD_ROUNDED, icon_color="white", icon_size=30,
            tooltip="Baixar Arquivo", url="", on_click=self._download_feedback
        )
        self.btn_close = ft.IconButton(ft.Icons.CLOSE, icon_color="white", icon_size=30, on_click=self.close)

        # Containers
        self.zoom_container = ft.InteractiveViewer(
            min_scale=0.1, max_scale=10.0, content=self.preview_img,
            boundary_margin=ft.Padding.all(5000), visible=False 
        )
        self.icon_container = ft.Container(content=self.preview_icn, alignment=ft.Alignment(0, 0), visible=False)

        # Gestos
        gesture_zone = ft.GestureDetector(
            content=ft.Container(
                content=ft.Stack([self.zoom_container, self.icon_container], alignment=ft.Alignment(0, 0)),
                alignment=ft.Alignment(0, 0), expand=True,
            ),
            on_horizontal_drag_end=self._on_pan_end,
            drag_interval=50
        )

        # Dialog
        self.dlg = ft.AlertDialog(
            modal=True, inset_padding=ft.Padding.all(0), bgcolor=ft.Colors.BLACK,
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        padding=10,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                            colors=[ft.Colors.BLACK54, ft.Colors.TRANSPARENT]
                        ),
                        content=ft.Row([self.btn_close, self.btn_download], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ),
                    ft.Container(content=gesture_zone, expand=True, alignment=ft.Alignment(0,0)),
                    ft.Container(
                        content=self.txt_info, padding=10, bgcolor=ft.Colors.BLACK54, 
                        border_radius=ft.BorderRadius.only(top_left=10, top_right=10), alignment=ft.Alignment(0, 0)
                    )
                ]),
                width=page.width, height=page.height, alignment=ft.Alignment(0, 0)
            ),
        )

    def register(self):
        # O pulo do gato: Adiciona ao overlay global da página
        self.page.overlay.append(self.dlg)
        self.page.on_keyboard_event = self._on_keyboard

    def open(self, files_list, start_filename):
        self.files_list = files_list
        try: self.current_index = self.files_list.index(start_filename)
        except: self.current_index = 0
        self.visible = True
        self.dlg.open = True
        self._update_ui()
        self.page.update()

    def close(self, e=None):
        self.visible = False
        self.dlg.open = False
        self.page.update()

    def _update_ui(self):
        if not self.files_list: return
        filename = self.files_list[self.current_index]
        data = get_file_details(filename)
        if not data: return

        self.txt_info.value = f"{data['name']}\n{data['size']} • {data['date']}"
        self.btn_download.url = data['full_url']
        self.btn_download.url_target = "_blank" 

        if data['is_img']:
            self.preview_img.src = data['url']
            self.zoom_container.visible = True
            self.icon_container.visible = False
            self.zoom_container.scale = 1.0 
        else:
            self.preview_icn.name = data['icon']
            self.preview_icn.color = data['color']
            self.zoom_container.visible = False
            self.icon_container.visible = True

    def _download_feedback(self, e):
        self.page.snack_bar = ft.SnackBar(ft.Text("Download iniciado..."), bgcolor="green")
        self.page.snack_bar.open = True
        self.page.update()

    def _navigate(self, delta):
        if not self.files_list: return
        self.current_index = (self.current_index + delta) % len(self.files_list)
        self._update_ui()
        self.page.update()

    def _on_keyboard(self, e: ft.KeyboardEvent):
        if self.visible:
            if e.key == "ArrowLeft": self._navigate(-1)
            elif e.key == "ArrowRight": self._navigate(1)
            elif e.key == "Escape": self.close()

    def _on_pan_end(self, e: ft.DragEndEvent):
        if e.primary_velocity is None: return
        if e.primary_velocity > 20: self._navigate(-1)
        elif e.primary_velocity < -20: self._navigate(1)