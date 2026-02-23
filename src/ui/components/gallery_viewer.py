import os
import flet as ft
from src.core.config import UPLOAD_ABS_PATH
from src.core.utils import get_file_details

class GalleryViewer:
    def __init__(self, page: ft.Page, on_file_click, log_callback=print):
        self.page = page
        self.on_file_click = on_file_click
        self.log = log_callback
        
        self.grid = ft.GridView(
            expand=True, runs_count=5, max_extent=150, 
            child_aspect_ratio=0.8, spacing=10, run_spacing=10,
        )

    def get_ui(self):
        return self.grid

    def refresh(self):
        self.grid.controls.clear()
        try:
            if not os.path.exists(UPLOAD_ABS_PATH):
                return []

            files = sorted(os.listdir(UPLOAD_ABS_PATH))
            if not files: 
                self.grid.controls.append(ft.Text("Nenhum arquivo.", color="grey"))
            
            for f in files:
                data = get_file_details(f)
                if not data: continue
                
                content_display = ft.Image(src=data['url'], fit="cover", border_radius=10, opacity=1) \
                    if data['is_img'] else ft.Icon(data['icon'], size=50, color=data['color'])

                self.grid.controls.append(
                    ft.Container(
                        bgcolor=ft.Colors.GREY_900, border_radius=10, padding=10,
                        on_click=lambda e, n=f: self.on_file_click(n),
                        ink=True,
                        content=ft.Column([
                            ft.Container(content=content_display, expand=True, alignment=ft.Alignment(0, 0)),
                            ft.Row([
                                ft.Text(f, size=10, no_wrap=True, max_lines=1, expand=True, overflow="ellipsis"),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_size=16, icon_color=ft.Colors.RED_400, on_click=lambda e, n=f: self._delete_file(n))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ])
                    )
                )
            self.page.update()
            return files
        except Exception as e:
            print(f"Erro ao listar galeria: {e}")
            return []

    def _delete_file(self, filename):
        path = os.path.join(UPLOAD_ABS_PATH, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                self.refresh()
            except Exception as e:
                print(f"Erro ao apagar: {e}")