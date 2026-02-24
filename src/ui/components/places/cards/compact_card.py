# ARQUIVO: src/ui/components/places/cards/compact_card.py
# CHANGE LOG:
# - Correção crítica: Substituído 'fit=ft.ImageFit.COVER' por 'fit="cover"' para resolver o erro que impedia os cards de carregarem.
# - Removido 'gapless_playback' para evitar que a imagem fique cinza no app Desktop.

import flet as ft

class CompactCard(ft.Stack):
    def __init__(self, item, current_user, images, on_click_callback, on_vote_callback):
        super().__init__()
        self.item = item
        self.current_user = current_user
        self.cb_click = on_click_callback
        self.cb_vote = on_vote_callback
        
        self.cover = images[0] if images and len(images) > 0 else "https://via.placeholder.com/300x200?text=Sem+Foto"
        
        self.controls = [
            self._build_card_background(),
            self._build_click_overlay(),
            self._build_like_button()
        ]

    def _build_card_background(self):
        try:
            raw = self.item.get("price", 0)
            val = float(str(raw).replace("R$", "").replace(",", ".").strip() or 0)
        except: val = 0.0

        return ft.Container(
            bgcolor=ft.Colors.GREY_900,
            border_radius=16, 
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=8, 
                color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK), 
                offset=ft.Offset(0, 4)
            ),
            content=ft.Column([
                ft.Stack([
                    ft.Image(
                        src=self.cover,
                        height=140,
                        width=float("inf"),
                        fit="cover" # <-- CORREÇÃO APLICADA AQUI
                    ),
                    # Gradiente sutil na base da foto
                    ft.Container(
                        bottom=0, height=40, width=float("inf"),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                            colors=[ft.Colors.TRANSPARENT, ft.Colors.BLACK87]
                        )
                    ),
                    ft.Container(
                        content=ft.Text(f"R$ {val:,.0f}", color=ft.Colors.WHITE, size=12, weight="bold"),
                        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREEN_700),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        border_radius=ft.border_radius.only(top_left=12, bottom_right=16),
                        bottom=0, right=0
                    )
                ]),
                
                ft.Container(
                    padding=ft.padding.only(left=12, right=12, top=10, bottom=14),
                    content=ft.Column([
                        ft.Text(
                            self.item.get("name", "Sem Nome"), 
                            weight="bold", size=15, color=ft.Colors.WHITE,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Row([
                            ft.Icon(ft.Icons.LOCATION_ON, size=14, color=ft.Colors.CYAN_400),
                            ft.Text(
                                self.item.get("address", "Local não informado"), 
                                size=12, color=ft.Colors.GREY_400, 
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True
                            )
                        ], spacing=4),
                    ], spacing=4)
                )
            ], spacing=0)
        )

    def _build_click_overlay(self):
        return ft.Container(
            expand=True,
            border_radius=16,
            ink=True,
            on_click=lambda _: self.cb_click(self.item)
        )

    def _build_like_button(self):
        votes = self.item.get("votes", [])
        has_voted = self.current_user in votes
        
        return ft.Container(
            bottom=12, right=12,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.FAVORITE if has_voted else ft.Icons.FAVORITE_BORDER,
                    icon_color=ft.Colors.RED_400 if has_voted else ft.Colors.WHITE70,
                    icon_size=20,
                    height=30, width=30,
                    style=ft.ButtonStyle(padding=0),
                    on_click=lambda e: self._handle_like(e)
                ),
                ft.Text(f"{len(votes)}", size=11, color=ft.Colors.WHITE if has_voted else ft.Colors.WHITE70, weight="bold")
            ], spacing=2)
        )

    def _handle_like(self, e):
        e.control.icon = ft.Icons.FAVORITE
        e.control.icon_color = ft.Colors.RED_400
        e.control.update()
        self.cb_vote(e, self.item)