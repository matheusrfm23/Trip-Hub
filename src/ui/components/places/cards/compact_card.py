import flet as ft

class CompactCard(ft.Stack):
    def __init__(self, item, current_user, images, on_click_callback, on_vote_callback):
        super().__init__()
        self.item = item
        self.current_user = current_user
        self.cb_click = on_click_callback
        self.cb_vote = on_vote_callback
        
        # Define capa
        self.cover = images[0] if images and len(images) > 0 else "https://via.placeholder.com/300x200?text=Sem+Foto"
        
        self.controls = [
            # 1. CAMADA VISUAL (Fundo)
            self._build_card_background(),
            
            # 2. CAMADA DE CLIQUE (Frente - Invisível)
            self._build_click_overlay(),
            
            # 3. BOTÃO DE LIKE (Topo - Clicável separadamente)
            self._build_like_button()
        ]

    def _build_card_background(self):
        # Tratamento de Preço
        try:
            raw = self.item.get("price", 0)
            val = float(str(raw).replace("R$", "").replace(",", ".").strip() or 0)
        except: val = 0.0

        return ft.Container(
            bgcolor=ft.Colors.GREY_900, # Fundo escuro elegante
            border_radius=12,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=10, 
                color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK), 
                offset=ft.Offset(0, 4)
            ),
            content=ft.Column([
                # Imagem + Badge
                ft.Stack([
                    ft.Image(
                        src=self.cover,
                        height=140,
                        width=float("inf"),
                        fit="cover",
                        gapless_playback=True
                    ),
                    # Badge de Preço
                    ft.Container(
                        content=ft.Text(f"R$ {val:,.0f}", color=ft.Colors.WHITE, size=12, weight="bold"),
                        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREEN_700),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=ft.border_radius.only(top_left=10, bottom_right=10),
                        bottom=0, right=0
                    )
                ]),
                
                # Infos
                ft.Container(
                    padding=12,
                    content=ft.Column([
                        ft.Text(
                            self.item.get("name", "Sem Nome"), 
                            weight="bold", size=16, color=ft.Colors.WHITE,
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
                    ], spacing=6)
                )
            ], spacing=0)
        )

    def _build_click_overlay(self):
        # Esta camada captura o clique principal para abrir o modal
        return ft.Container(
            expand=True,
            border_radius=12,
            ink=True,
            on_click=lambda _: self.cb_click(self.item)
        )

    def _build_like_button(self):
        votes = self.item.get("votes", [])
        has_voted = self.current_user in votes
        
        return ft.Container(
            bottom=10, right=10,
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.FAVORITE if has_voted else ft.Icons.FAVORITE_BORDER,
                    icon_color=ft.Colors.RED_400 if has_voted else ft.Colors.GREY_500,
                    icon_size=20,
                    height=30, width=30,
                    style=ft.ButtonStyle(padding=0), # Remove padding extra
                    on_click=lambda e: self._handle_like(e)
                ),
                ft.Text(f"{len(votes)}", size=11, color=ft.Colors.GREY_500)
            ], spacing=2)
        )

    def _handle_like(self, e):
        # Feedback visual instantâneo
        e.control.icon = ft.Icons.FAVORITE
        e.control.icon_color = ft.Colors.RED_400
        e.control.update()
        self.cb_vote(e, self.item)