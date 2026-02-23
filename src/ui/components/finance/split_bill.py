import flet as ft

class SplitBillCard(ft.Card):
    def __init__(self):
        super().__init__(elevation=10)
        
        self.split_total = ft.TextField(
            label="Total Conta", expand=True, keyboard_type=ft.KeyboardType.NUMBER, 
            prefix_icon=ft.Icons.ATTACH_MONEY, height=48, text_size=14, content_padding=10, dense=True,
            on_change=self._on_money_change
        )
        self.split_people = ft.TextField(
            label="Pessoas", width=100, keyboard_type=ft.KeyboardType.NUMBER, 
            icon=ft.Icons.PEOPLE, height=48, text_size=14, content_padding=10, value="0", dense=True,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")
        )
        self.split_service = ft.TextField(
            label="Taxa %", width=80, keyboard_type=ft.KeyboardType.NUMBER,
            height=48, text_size=14, content_padding=10, value="10", dense=True
        )
        self.split_couvert_val = ft.TextField(
            label="Couvert", expand=True, keyboard_type=ft.KeyboardType.NUMBER, 
            height=48, text_size=14, content_padding=10, value="", dense=True,
            on_change=self._on_money_change
        )
        self.split_couvert_type = ft.Dropdown(
            width=70, height=48, text_size=14, content_padding=10,
            options=[ft.dropdown.Option("R$"), ft.dropdown.Option("%")],
            value="R$", border_radius=8, dense=True
        )
        
        self.split_people.on_change = self._calc_split
        self.split_service.on_change = self._calc_split
        self.split_couvert_type.on_change = self._calc_split

        self.split_result_text = ft.Text("R$ 0,00 / pessoa", weight="bold", color=ft.Colors.WHITE, size=15)

        self.content = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[ft.Colors.ORANGE_900, ft.Colors.BLACK]
            ),
            border_radius=12, padding=0, border=ft.border.all(1, ft.Colors.WHITE10),
            content=ft.ExpansionTile(
                leading=ft.Icon(ft.Icons.LOCAL_BAR, color=ft.Colors.ORANGE_ACCENT, size=24),
                title=ft.Text("Dividir Conta", weight="bold", size=14, color=ft.Colors.WHITE),
                subtitle=self.split_result_text,
                controls=[
                    ft.Container(
                        padding=15,
                        content=ft.Column([
                            ft.Row([self.split_total, self.split_people], spacing=10),
                            ft.Row([self.split_service, self.split_couvert_val, self.split_couvert_type], spacing=10, alignment="center"),
                            ft.Text("Digite apenas números. O sistema formata centavos automaticamente.", size=10, color=ft.Colors.WHITE54, italic=True)
                        ], spacing=15)
                    )
                ]
            )
        )

    def _parse_money_str(self, val_str):
        if not val_str: return 0.0
        clean = val_str.replace(".", "").replace(",", ".")
        try: return float(clean)
        except: return 0.0

    def _format_money_live(self, e):
        raw_val = "".join(filter(str.isdigit, e.control.value))
        if not raw_val or int(raw_val) == 0:
            e.control.value = ""
            e.control.update()
            return
        val_float = int(raw_val) / 100
        formatted = "{:,.2f}".format(val_float).replace(",", "X").replace(".", ",").replace("X", ".")
        e.control.value = formatted
        e.control.update()

    def _on_money_change(self, e):
        self._format_money_live(e)
        self._calc_split(None)

    def _calc_split(self, e):
        try:
            total_consumo = self._parse_money_str(self.split_total.value)
            pessoas = int(self.split_people.value or "1")
            if pessoas <= 0: pessoas = 1
            
            taxa_input = self.split_service.value.replace(",", ".") or "0"
            taxa_pct = float(taxa_input) / 100
            
            couvert_val = self._parse_money_str(self.split_couvert_val.value)
            couvert_type = self.split_couvert_type.value 
            
            valor_servico = total_consumo * taxa_pct
            
            if couvert_type == "%": 
                valor_couvert = total_consumo * (couvert_val / 100)
            else: 
                valor_couvert = couvert_val * pessoas
            
            total_final = total_consumo + valor_servico + valor_couvert
            por_cabeca = total_final / pessoas
            self.split_result_text.value = f"R$ {por_cabeca:,.2f} / pessoa".replace(",", "X").replace(".", ",").replace("X", ".")
            self.split_result_text.update()
        except: pass