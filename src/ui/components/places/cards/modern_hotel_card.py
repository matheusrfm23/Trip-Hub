import flet as ft
from src.ui.components.common.image_carousel import ImageCarousel

class ModernHotelCard(ft.Container):
    def __init__(self, item, is_admin, images, callbacks):
        """
        Card 'Logística de Viagem' - Versão Completa para Hospedagem
        """
        super().__init__(
            padding=0,
            border_radius=16,
            bgcolor=ft.Colors.GREY_900,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.BLACK45, offset=ft.Offset(0, 4)),
            on_click=None
        )
        
        self.item = item
        self.is_admin = is_admin
        self.images = images
        self.cb = callbacks
        
        self.content = self._build_layout()

    def _build_layout(self):
        return ft.Column([
            # 1. Carrossel
            ImageCarousel(
                images=self.images,
                is_admin=self.is_admin,
                height=220,
                on_zoom=self.cb.get('on_zoom'),
                on_delete_photo=self.cb.get('on_delete_photo')
            ),
            
            # 2. Informações
            ft.Container(
                padding=15,
                content=ft.Column([
                    self._build_header(),
                    
                    # [NOVO] Bloco de Datas Destacado
                    self._build_dates_display(),
                    
                    ft.Divider(height=20, color=ft.Colors.WHITE10),
                    self._build_address(),
                ], spacing=5)
            ),
            
            # 3. Painel Expansível
            self._build_expandable_details(),
            
            # 4. Rodapé Admin
            self._build_footer()
        ], spacing=0)

    def _build_header(self):
        return ft.Row([
            ft.Text(self.item.get("name", "Hospedagem"), size=22, weight="bold", expand=True),
            ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.GREY_600, tooltip="Editar", 
                          on_click=lambda e: self.cb['on_edit'](self.item))
        ], alignment="spaceBetween")

    def _build_dates_display(self):
        """Mostra Check-in e Check-out de forma clara"""
        checkin = self.item.get('checkin', '--/--')
        checkout = self.item.get('checkout', '--/--')
        
        return ft.Container(
            bgcolor=ft.Colors.BLUE_GREY_900,
            border_radius=8,
            padding=10,
            content=ft.Row([
                ft.Column([
                    ft.Text("ENTRADA", size=10, color=ft.Colors.GREY_400, weight="bold"),
                    ft.Row([ft.Icon(ft.Icons.LOGIN, size=16, color=ft.Colors.GREEN_400), ft.Text(checkin, weight="bold")], spacing=5)
                ]),
                ft.Container(width=1, height=30, bgcolor=ft.Colors.GREY_700), # Separador
                ft.Column([
                    ft.Text("SAÍDA", size=10, color=ft.Colors.GREY_400, weight="bold"),
                    ft.Row([ft.Icon(ft.Icons.LOGOUT, size=16, color=ft.Colors.ORANGE_400), ft.Text(checkout, weight="bold")], spacing=5)
                ])
            ], alignment="spaceAround")
        )

    def _build_address(self):
        return ft.Container(
            bgcolor=ft.Colors.BLACK26, border_radius=8, padding=10,
            content=ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED_400),
                ft.Text(self.item.get("address", ""), size=14, color=ft.Colors.WHITE70, expand=True, max_lines=2),
                ft.IconButton(ft.Icons.COPY, icon_color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_GREY_700, 
                              on_click=lambda e: self.cb['on_copy'](self.item.get("address")))
            ], alignment="spaceBetween")
        )

    def _build_expandable_details(self):
        # WiFi
        wifi_info = ft.Container()
        ssid = self.item.get('wifi')
        if ssid:
            wifi_info = ft.Container(
                bgcolor=ft.Colors.BLUE_900, padding=10, border_radius=8, margin=ft.margin.only(bottom=10),
                content=ft.Row([
                    ft.Icon(ft.Icons.WIFI, color=ft.Colors.WHITE),
                    ft.Column([
                        ft.Text(f"Rede: {ssid}", weight="bold"),
                        ft.Text(f"Senha: {self.item.get('wifi_pass','-')}", font_family="Consolas")
                    ], spacing=2)
                ])
            )

        # Checklist
        def make_check(label, key, icon):
            has_it = self.item.get(key, False)
            color = ft.Colors.GREEN_400 if has_it else ft.Colors.GREY_700
            ic = icon if has_it else ft.Icons.CANCEL_OUTLINED
            op = 1.0 if has_it else 0.3
            return ft.Container(opacity=op, content=ft.Row([
                ft.Icon(ic, size=18, color=color),
                ft.Text(label, size=13, color=ft.Colors.WHITE if has_it else ft.Colors.GREY_500)
            ], spacing=5))

        items = [
            make_check("Toalhas", "has_towels", ft.Icons.DRY_CLEANING),
            make_check("Roupa Cama", "has_linen", ft.Icons.BED),
            make_check("Chuveiro Quente", "has_hot_shower", ft.Icons.SHOWER),
            make_check("Piscina", "has_pool", ft.Icons.POOL),
            make_check("Ar Cond.", "has_ac", ft.Icons.AC_UNIT),
            make_check("Garagem", "has_parking", ft.Icons.DIRECTIONS_CAR),
            make_check("Cozinha", "has_kitchen", ft.Icons.KITCHEN),
            make_check("Smart TV", "has_tv", ft.Icons.TV)
        ]
        
        checklist = ft.Row(controls=items, wrap=True, spacing=15, run_spacing=10)

        return ft.ExpansionTile(
            title=ft.Text("Ver Comodidades", color=ft.Colors.CYAN_200, weight="bold"),
            leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.CYAN_200),
            bgcolor=ft.Colors.GREY_900, collapsed_bgcolor=ft.Colors.GREY_900,
            controls=[
                ft.Container(
                    padding=15, bgcolor=ft.Colors.BLACK26,
                    content=ft.Column([
                        wifi_info,
                        ft.Text("ITENS DA CASA:", size=12, weight="bold", color=ft.Colors.GREY_500),
                        checklist,
                        ft.Divider(color=ft.Colors.WHITE10),
                        ft.Text("OBSERVAÇÕES:", size=12, weight="bold", color=ft.Colors.GREY_500),
                        ft.Text(self.item.get("description", "---"), size=13, color=ft.Colors.GREY_300)
                    ])
                )
            ]
        )

    def _build_footer(self):
        if not self.is_admin: return ft.Container()
        return ft.Container(
            padding=10, bgcolor=ft.Colors.BLACK12,
            content=ft.Row([
                ft.TextButton("Mapa", icon=ft.Icons.MAP, on_click=lambda e: self.cb['on_open_map'](self.item.get("maps_link"))),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.ADD_A_PHOTO, icon_color=ft.Colors.CYAN_200, 
                              on_click=lambda e: self.cb['on_add_photo'](self.item["id"])),
                ft.Container(width=10),
                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_300, 
                              on_click=lambda e: self.cb['on_delete'](self.item))
            ])
        )