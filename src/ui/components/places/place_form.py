import flet as ft

class PlaceForm:
    def __init__(self, page: ft.Page, on_save_callback):
        self.page = page
        self.on_save = on_save_callback
        self.dialog = None 
        self.item_id = None
        self.category = None # Armazena categoria para usar no callback
        
        self.name_field = ft.TextField(label="Nome do Local", border_color=ft.Colors.CYAN)
        self.address_field = ft.TextField(label="Endereço", multiline=True, min_lines=2)
        self.maps_link_field = ft.TextField(label="Link Maps", icon=ft.Icons.LINK)
        
        self.price_field = ft.TextField(
            label="Preço Médio", 
            prefix_text="R$ ",
            keyboard_type=ft.KeyboardType.NUMBER, 
            width=140
        )
        
        self.desc_field = ft.TextField(label="Descrição / Notas", multiline=True)

        # Campos de Hospedagem (Datas Claras)
        self.checkin_field = ft.TextField(label="Dia de Entrada (Check-in)", hint_text="Ex: 20/12 às 14h", icon=ft.Icons.LOGIN)
        self.checkout_field = ft.TextField(label="Dia de Saída (Check-out)", hint_text="Ex: 27/12 às 11h", icon=ft.Icons.LOGOUT)
        
        self.wifi_ssid = ft.TextField(label="Rede WiFi", prefix_icon=ft.Icons.WIFI)
        self.wifi_pass = ft.TextField(label="Senha WiFi") 
        
        self.switches = {
            "has_towels": ft.Switch(label="Toalhas"),
            "has_linen": ft.Switch(label="Roupa Cama"),
            "has_hot_shower": ft.Switch(label="Chuveiro Quente"),
            "has_pool": ft.Switch(label="Piscina"),
            "has_ac": ft.Switch(label="Ar Cond."),
            "has_parking": ft.Switch(label="Garagem"),
            "has_kitchen": ft.Switch(label="Cozinha"),
            "has_tv": ft.Switch(label="TV Smart")
        }

    def open(self, category, item=None):
        self.category = category
        self.item_id = item["id"] if item else None
        is_hotel = (category == "hotel")
        
        # Popula campos baseado no item ou limpa
        self._populate_fields(item, is_hotel)

        # Constrói o conteúdo dinamicamente
        content_controls = [
            ft.Text("Editar" if item else "Novo Local", size=20, weight="bold", color=ft.Colors.CYAN),
            ft.Divider(),
            self.name_field,
            self.address_field,
            self.maps_link_field,
            ft.Row([self.price_field]),
            ft.Divider(),
            self.desc_field
        ]

        # Se for hotel, insere campos extras no meio da lista
        if is_hotel:
            # Índices podem variar, mas vamos adicionar após o preço/descrição
            extra_hotel = [
                ft.Divider(height=10, color="transparent"),
                ft.Text("Datas da Viagem", weight="bold", color=ft.Colors.ORANGE_300),
                self.checkin_field,
                self.checkout_field,
                ft.Divider(),
                ft.Text("Conectividade", weight="bold"),
                self.wifi_ssid,
                self.wifi_pass,
                ft.Divider(),
                ft.Text("Comodidades Disponíveis", weight="bold", color=ft.Colors.CYAN_200),
                
                ft.Container(
                    content=ft.Row(
                        controls=list(self.switches.values()),
                        wrap=True,      
                        spacing=10,
                        run_spacing=10
                    ),
                    padding=5
                )
            ]
            # Insere antes do divider final e botão salvar
            content_controls.extend(extra_hotel)

        content_controls.append(ft.Container(height=20))

        # Botão Salvar
        btn_save = ft.ElevatedButton(
            "Salvar",
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.CYAN,
            color=ft.Colors.BLACK,
            on_click=self._save_click,
            width=200
        )

        content_controls.append(ft.Container(content=btn_save, alignment=ft.Alignment(0,0)))

        # Cria o Dialog
        self.dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(content_controls, scroll=ft.ScrollMode.AUTO),
                width=400,
                height=600,
                padding=10
            ),
            actions=[ft.TextButton("Cancelar", on_click=self._close)]
        )
        
        # [MODERNO] Abre usando self.page.open()
        self.page.open(self.dialog)

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
        else:
            # Reseta switches se não for hotel
             for key, sw in self.switches.items():
                sw.value = False

    def _save_click(self, e):
        if not self.name_field.value:
            self.name_field.error_text = "Nome obrigatório"
            self.name_field.update()
            return

        data = {
            "name": self.name_field.value,
            "address": self.address_field.value,
            "maps_link": self.maps_link_field.value,
            "price": self.price_field.value,
            "description": self.desc_field.value,
            "category": self.category # Garante que a categoria vai junto
        }
        
        # Campos opcionais (Hotel)
        data["checkin"] = self.checkin_field.value
        data["checkout"] = self.checkout_field.value
        data["wifi"] = self.wifi_ssid.value
        data["wifi_pass"] = self.wifi_pass.value
        
        for key, sw in self.switches.items():
            data[key] = sw.value
        
        # [MODERNO] Fecha usando self.page.close()
        self.page.close(self.dialog)

        # Chama callback (Geralmente update na lista)
        if self.on_save:
            # Passa item_id se for edição, ou None se for novo
            self.on_save(self.item_id, data)

    def _close(self, e=None):
        # [MODERNO] Fecha usando self.page.close()
        if self.dialog:
            self.page.close(self.dialog)