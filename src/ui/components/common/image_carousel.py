# ARQUIVO: src/ui/components/common/image_carousel.py
# CHANGE LOG:
# - Correção de AttributeError trocando ft.ImageFit.COVER por "cover" (compatibilidade de versão).

import flet as ft

class ImageCarousel(ft.Stack):
    def __init__(self, images, is_admin, height=200, border_radius=0, on_zoom=None, on_delete_photo=None):
        super().__init__()
        self.images = images if images and isinstance(images, list) else ["https://via.placeholder.com/400x300?text=Sem+Foto"]
        self.is_admin = is_admin
        self.height_val = height
        self.radius_val = border_radius
        self.on_zoom = on_zoom
        self.on_delete_photo = on_delete_photo
        
        self.current_index = 0
        self.total_images = len(self.images)
        
        # Imagem principal (sem gapless_playback para evitar bug no Desktop)
        self.img_control = ft.Image(
            src=self.images[0],
            height=self.height_val,
            width=float("inf"),
            fit="cover",
            border_radius=self.radius_val
        )
        
        # Contador (1/5)
        self.counter_badge = ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            bgcolor=ft.Colors.with_opacity(0.7, ft.Colors.BLACK),
            border_radius=12,
            content=ft.Text(f"1/{self.total_images}", color=ft.Colors.WHITE, size=11, weight="bold"),
            visible=self.total_images > 1 
        )

        self.controls = self._build_controls()

    def _build_controls(self):
        layers = [
            ft.GestureDetector(
                content=self.img_control,
                on_tap=self._on_image_tap
            )
        ]

        if self.total_images > 1:
            layers.append(
                ft.Container(
                    content=ft.IconButton(
                        ft.Icons.CHEVRON_LEFT, 
                        icon_color=ft.Colors.WHITE, 
                        bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
                        on_click=lambda e: self._navigate(-1),
                    ),
                    alignment=ft.Alignment(-1, 0),
                    padding=ft.padding.only(left=8),
                    height=self.height_val,
                    width=60,
                )
            )

            layers.append(
                ft.Container(
                    content=ft.IconButton(
                        ft.Icons.CHEVRON_RIGHT, 
                        icon_color=ft.Colors.WHITE, 
                        bgcolor=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
                        on_click=lambda e: self._navigate(1),
                    ),
                    alignment=ft.Alignment(1, 0),
                    padding=ft.padding.only(right=8),
                    height=self.height_val,
                    right=0
                )
            )
            
            layers.append(ft.Container(content=self.counter_badge, top=12, right=12))

        if self.is_admin and self.on_delete_photo and self.total_images > 0:
            layers.append(
                ft.Container(
                    content=ft.IconButton(
                        ft.Icons.DELETE_FOREVER, 
                        icon_color=ft.Colors.WHITE, 
                        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.RED_700),
                        icon_size=20,
                        on_click=lambda e: self.on_delete_photo(self.images[self.current_index])
                    ),
                    top=12, left=12
                )
            )

        return layers

    def _navigate(self, delta):
        new_index = self.current_index + delta
        if 0 <= new_index < self.total_images:
            self.current_index = new_index
            self.img_control.src = self.images[self.current_index]
            self.counter_badge.content.value = f"{self.current_index + 1}/{self.total_images}"
            self.counter_badge.update()
            self.img_control.update()

    def _on_image_tap(self, e):
        if self.on_zoom:
            self.on_zoom(self.images[self.current_index])