# ARQUIVO: src/ui/components/places/cards/modern_hotel_card.py
# CHANGE LOG:
# - UI refinada para Mobile: Painéis mais suaves, melhor hierarquia visual.

import flet as ft
from src.ui.components.common.image_carousel import ImageCarousel

class ModernHotelCard(ft.Container):
    def __init__(self, item, is_admin, images, callbacks):
        super().__init__(
            padding=0,
            border_radius=16,
            bgcolor=ft.Colors.GREY_900,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color=ft.Colors.BLACK45, offset=ft.Offset(0, 4)),
            margin=ft.margin.only(bottom=10)
        )
        
        self.item = item
        self.is_admin = is_admin
        self.images = images
        self.cb = callbacks
        
        self.content = self._build_layout()

    def _build_layout(self):
        return ft.Column([
            ImageCarousel(
                images=self.images,
                is_admin=self.is_admin,
                height=220,
                on_zoom=self.cb.get('on_zoom'),
                on_delete_photo=self.cb.get('on_delete_photo')
            ),
            
            ft.Container(
                padding=16,
                content=ft.Column([
                    self._build_header(),
                    ft.Container(height=5),
                    self._build_dates_display(),
                    ft.Divider(height=24, color=ft.Colors.WHITE10),
                    self._build_address(),
                ], spacing=0)
            ),
            
            self._build_expandable_details(),
            self._build_footer()
        ], spacing=0)

    def _build_header(self):
        return ft.Row([
            ft.Text(self.item.get("name", "Hospedagem"), size=20, weight="bold", expand=True),
            ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.GREY_500, tooltip="Editar", 
                          on_click=lambda e: self.cb['on_edit'](self.item))
        ], alignment="spaceBetween")

    def _build_dates_display(self):
        checkin = self.item.get('checkin', '--/--')
        checkout = self.item.get('checkout', '--/--')
        
        return ft.Container(
            bgcolor=ft.Colors.BLACK26,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            content=ft.Row([
                ft.Column([
                    ft.Text("CHECK-IN", size=10, color=ft.Colors.GREY_500, weight="w700"),
                    ft.Row([ft.Icon(ft.Icons.LOGIN, size=18, color=ft.Colors.GREEN_400), ft.Text(checkin, weight="bold", size=15)], spacing=6)
                ], expand=True),
                
                ft.Container(width=1, height=35, bgcolor=ft.Colors.WHITE10), 
                
                ft.Column([
                    ft.Text("CHECK-OUT", size=10, color=ft.Colors.GREY_500, weight="w700"),
                    ft.Row([ft.Icon(ft.Icons.LOGOUT, size=18, color=ft.Colors.ORANGE_400), ft.Text(checkout, weight="bold", size=15)], spacing=6)
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.END)
            ], alignment="spaceBetween")
        )

    def _build_address(self):
        return ft.Row([
            ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED_400, size=20),
            ft.Text(self.item.get("address", ""), size=13, color=ft.Colors.WHITE70, expand=True, max_lines=2),
            ft.IconButton(ft.Icons.COPY, icon_color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_GREY_800, 
                          icon_size=16, on_click=lambda e: self.cb['on_copy'](self.item.get("address")))
        ], alignment="spaceBetween", spacing=10)

    def _build_expandable_details(self):
        wifi_info = ft.Container()
        ssid = self.item.get('wifi')
        if ssid:
            wifi_info = ft.Container(
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN), padding=12, border_radius=12, margin=ft.margin.only(bottom=15),
                border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.CYAN)),
                content=ft.Row([
                    ft.Icon(ft.Icons.WIFI, color=ft.Colors.CYAN_300),
                    ft.Column([
                        ft.Text(f"Rede: {ssid}", weight="bold", color=ft.Colors.WHITE),
                        ft.Text(f"Senha: {self.item.get('wifi_pass','-')}", font_family="Consolas", color=ft.Colors.CYAN_100)
                    ], spacing=2)
                ])
            )

        def make_check(label, key, icon):
            has_it = self.item.get(key, False)
            color = ft.Colors.CYAN_400 if has_it else ft.Colors.GREY_700
            ic = icon if has_it else ft.Icons.CANCEL_OUTLINED
            return ft.Container(
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                bgcolor=ft.Colors.BLACK26 if has_it else ft.Colors.TRANSPARENT,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.WHITE10) if not has_it else None,
                content=ft.Row([
                    ft.Icon(ic, size=16, color=color),
                    ft.Text(label, size=12, color=ft.Colors.WHITE if has_it else ft.Colors.GREY_500)
                ], spacing=6)
            )

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
        
        checklist = ft.Row(controls=items, wrap=True, spacing=10, run_spacing=10)

        return ft.ExpansionTile(
            title=ft.Text("Comodidades e Info", color=ft.Colors.CYAN_200, weight="bold", size=14),
            leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.CYAN_200),
            bgcolor=ft.Colors.GREY_900, collapsed_bgcolor=ft.Colors.GREY_900,
            controls=[
                ft.Container(
                    padding=16, bgcolor=ft.Colors.BLACK12,
                    content=ft.Column([
                        wifi_info,
                        ft.Text("ITENS DA CASA:", size=11, weight="bold", color=ft.Colors.GREY_500),
                        checklist,
                        ft.Divider(color=ft.Colors.WHITE10, height=20),
                        ft.Text("OBSERVAÇÕES:", size=11, weight="bold", color=ft.Colors.GREY_500),
                        ft.Text(self.item.get("description", "Sem observações adicionais."), size=13, color=ft.Colors.GREY_300)
                    ])
                )
            ]
        )

    def _build_footer(self):
        if not self.is_admin: return ft.Container()
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=10), bgcolor=ft.Colors.BLACK26,
            content=ft.Row([
                ft.TextButton("Abrir Mapa", icon=ft.Icons.MAP, icon_color=ft.Colors.BLUE_400, style=ft.ButtonStyle(color=ft.Colors.BLUE_400), on_click=lambda e: self.cb['on_open_map'](self.item.get("maps_link"))),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.ADD_A_PHOTO, icon_color=ft.Colors.CYAN_300, 
                              on_click=lambda e: self.cb['on_add_photo'](self.item["id"])),
                ft.Container(width=5),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, 
                              on_click=lambda e: self.cb['on_delete'](self.item))
            ])
        )