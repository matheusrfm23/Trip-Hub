# ARQUIVO: src/ui/components/places/place_form.py
# CHANGE LOG:
# - Formulário modernizado com border_radius, filled=True, agrupamento de datas e layout fluido para Mobile.

import flet as ft

class PlaceForm:
    def __init__(self, page: ft.Page, on_save_callback):
        self.page = page
        self.on_save = on_save_callback
        self.dialog = None 
        self.item_id = None
        
        # Campos Modernizados
        def create_field(label, icon=None, prefix=None, **kwargs):
            return ft.TextField(
                label=label, 
                prefix_icon=icon, 
                prefix=prefix,
                border_radius=12, 
                filled=True, 
                bgcolor=ft.Colors.BLACK26,
                border_color=ft.Colors.CYAN_700,
                focused_border_color=ft.Colors.CYAN_300,
                text_size=14,
                **kwargs
            )

        self.name_field = create_field("Nome do Local", icon=ft.Icons.TITLE)
        self.address_field = create_field("Endereço", multiline=True, min_lines=2, icon=ft.Icons.LOCATION_ON)
        self.maps_link_field = create_field("Link Google Maps", icon=ft.Icons.LINK)
        
        self.price_field = create_field("Preço", prefix=ft.Text("R$ "), keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        self.desc_field = create_field("Descrição / Notas", multiline=True, min_lines=2)

        # Campos de Hospedagem
        self.checkin_field = create_field("Check-in", hint_text="20/12 14h", expand=True)
        self.checkout_field = create_field("Check-out", hint_text="27/12 11h", expand=True)
        
        self.wifi_ssid = create_field("Rede WiFi", icon=ft.Icons.WIFI, expand=True)
        self.wifi_pass = create_field("Senha WiFi", icon=ft.Icons.PASSWORD, expand=True) 
        
        self.switches = {
            "has_towels": ft.Switch(label="Toalhas", active_color=ft.Colors.CYAN),
            "has_linen": ft.Switch(label="Cama", active_color=ft.Colors.CYAN),
            "has_hot_shower": ft.Switch(label="Chuveiro", active_color=ft.Colors.CYAN),
            "has_pool": ft.Switch(label="Piscina", active_color=ft.Colors.CYAN),
            "has_ac": ft.Switch(label="Ar Cond.", active_color=ft.Colors.CYAN),
            "has_parking": ft.Switch(label="Vaga", active_color=ft.Colors.CYAN),
            "has_kitchen": ft.Switch(label="Cozinha", active_color=ft.Colors.CYAN),
            "has_tv": ft.Switch(label="TV Smart", active_color=ft.Colors.CYAN)
        }

    def open(self, category, item=None):
        self.item_id = item["id"] if item else None
        is_hotel = (category == "hotel")
        
        self._populate_fields(item, is_hotel)

        content_controls = [
            ft.Text("Editar Local" if item else "Novo Local", size=22, weight="bold", color=ft.Colors.CYAN_300),
            ft.Divider(color=ft.Colors.WHITE10),
            self.name_field,
            self.address_field,
            self.maps_link_field,
            ft.Row([self.price_field], expand=True),
            self.desc_field
        ]

        if is_hotel:
            extra_hotel = [
                ft.Divider(height=20, color=ft.Colors.WHITE10),
                ft.Text("Datas da Viagem", weight="bold", color=ft.Colors.ORANGE_300, size=12),
                ft.Row([self.checkin_field, self.checkout_field], spacing=10),
                
                ft.Container(height=10),
                ft.Text("Conectividade", weight="bold", color=ft.Colors.CYAN_200, size=12),
                ft.Row([self.wifi_ssid, self.wifi_pass], spacing=10),
                
                ft.Container(height=10),
                ft.Text("Comodidades Disponíveis", weight="bold", color=ft.Colors.CYAN_200, size=12),
                ft.Container(
                    bgcolor=ft.Colors.BLACK26, border_radius=12, padding=10,
                    content=ft.Row(
                        controls=list(self.switches.values()),
                        wrap=True,      
                        spacing=10,
                        run_spacing=5
                    )
                )
            ]
            content_controls.extend(extra_hotel)

        content_controls.append(ft.Container(height=10))
        content_controls.append(
            ft.ElevatedButton("SALVAR INFORMAÇÕES", icon=ft.Icons.CHECK, bgcolor=ft.Colors.CYAN_600, color=ft.Colors.WHITE, height=50, on_click=self._save, width=float("inf"))
        )

        self.dialog = ft.AlertDialog(
            bgcolor=ft.Colors.GREY_900,
            shape=ft.RoundedRectangleBorder(radius=16),
            content_padding=20,
            content=ft.Container(
                content=ft.Column(content_controls, scroll=ft.ScrollMode.AUTO, spacing=10),
                width=450,
                height=650
            ),
            actions=[ft.TextButton("Cancelar", on_click=self._close, style=ft.ButtonStyle(color=ft.Colors.GREY_400))]
        )
        
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _populate_fields(self, item, is_hotel):
        if not item: item = {}
        
        self.name_field.value = item.get("name", "")
        self.address_field.value = item.get("address", "")
        self.maps_link_field.value = item.get("maps_link", "")
        self.price_field.value = str(item.get("price", ""))
        self.desc_field.value = item.get("description", "")
        
        if is_hotel:
            self.checkin_field.value = item.get("checkin", "")
            self.checkout_field.value = item.get("checkout", "")
            self.wifi_ssid.value = item.get("wifi", "")
            self.wifi_pass.value = item.get("wifi_pass", "")
            
            for key, sw in self.switches.items():
                sw.value = item.get(key, False)

    def _save(self, e):
        if not self.name_field.value:
            self.name_field.error_text = "Obrigatório"
            self.name_field.update()
            return

        data = {
            "name": self.name_field.value,
            "address": self.address_field.value,
            "maps_link": self.maps_link_field.value,
            "price": self.price_field.value,
            "description": self.desc_field.value,
        }
        
        data["checkin"] = self.checkin_field.value
        data["checkout"] = self.checkout_field.value
        data["wifi"] = self.wifi_ssid.value
        data["wifi_pass"] = self.wifi_pass.value
        
        for key, sw in self.switches.items():
            data[key] = sw.value
        
        self._close()
        self.page.run_task(self.on_save, self.item_id, data)

    def _close(self, e=None):
        self.dialog.open = False
        self.page.update()