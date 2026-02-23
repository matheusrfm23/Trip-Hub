import flet as ft
from src.logic.finance_service import FinanceService

class ConverterCard(ft.Card):
    def __init__(self):
        super().__init__(elevation=5)
        
        self.calc_from = ft.Dropdown(label="De", width=100, value="USD", height=48, content_padding=10, text_size=14, options=[ft.dropdown.Option(x) for x in ["BRL", "USD", "ARS", "PYG"]], border_radius=8)
        self.calc_from.on_change = self._calc_convert
        self.calc_to = ft.Dropdown(label="Para", width=100, value="BRL", height=48, content_padding=10, text_size=14, options=[ft.dropdown.Option(x) for x in ["BRL", "USD", "ARS", "PYG"]], border_radius=8)
        self.calc_to.on_change = self._calc_convert
        
        self.calc_amount = ft.TextField(
            label="Valor", expand=True, keyboard_type=ft.KeyboardType.NUMBER,
            text_style=ft.TextStyle(size=16, weight="bold"),
            border_color=ft.Colors.CYAN, prefix_icon=ft.Icons.MONETIZATION_ON,
            height=48, content_padding=10,
            on_change=self._on_money_change
        )
        
        self.calc_result_str = ft.Text("0.00", size=14, weight="bold", color=ft.Colors.CYAN_200)
        
        self.content = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[ft.Colors.BLUE_GREY_900, ft.Colors.BLACK]
            ),
            border_radius=12, padding=0, border=ft.border.all(1, ft.Colors.WHITE10),
            content=ft.ExpansionTile(
                leading=ft.Icon(ft.Icons.CURRENCY_EXCHANGE, color=ft.Colors.CYAN, size=24),
                title=ft.Text("Conversor", weight="bold", size=14, color=ft.Colors.WHITE),
                subtitle=self.calc_result_str,
                controls=[
                    ft.Container(
                        padding=15,
                        content=ft.Column([
                            ft.Row([self.calc_from, ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=ft.Colors.GREY), self.calc_to], alignment="center", spacing=5),
                            ft.Container(height=5),
                            ft.Row([self.calc_amount])
                        ], spacing=5)
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
        self._calc_convert(None)

    def _calc_convert(self, e):
        try:
            val = self._parse_money_str(self.calc_amount.value)
            res = FinanceService.convert_value(val, self.calc_from.value, self.calc_to.value)
            result_txt = f"{res:,.2f} {self.calc_to.value}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.calc_result_str.value = result_txt
            self.calc_result_str.update()
        except: pass