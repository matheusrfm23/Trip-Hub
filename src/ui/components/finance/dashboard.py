import flet as ft
from src.logic.finance_service import FinanceService

class FinanceDashboard:
    def __init__(self):
        # Linha de Cotações (Ticker) com scroll horizontal
        self.rates_row = ft.Row(spacing=10, scroll=ft.ScrollMode.HIDDEN)
        
        # Cards de Resumo
        self.total_card = self._build_stat_card("Total Grupo", "R$ ...", ft.Icons.GROUPS, ft.Colors.AMBER_700)
        self.balance_card = self._build_stat_card("Meu Saldo", "R$ ...", ft.Icons.WALLET, ft.Colors.GREEN_700)

    def _build_stat_card(self, title, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, color=color, size=16), ft.Text(title, size=11, color=ft.Colors.GREY_400)]),
                ft.Text(value, size=18, weight="bold")
            ], spacing=2),
            bgcolor=ft.Colors.WHITE10, padding=12, border_radius=10, expand=True
        )

    def update_stats(self, report):
        """Atualiza os valores dos cards"""
        try:
            # Formatação segura
            grp = report.get('group_total', 0) or report.get('total_group_brl', 0)
            bal = report.get('my_balance', 0) or report.get('user_balance', 0)

            grp_fmt = f"R$ {grp:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            bal_fmt = f"R$ {bal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            self.total_card.content.controls[1].value = grp_fmt
            
            self.balance_card.content.controls[1].value = bal_fmt
            self.balance_card.content.controls[1].color = ft.Colors.GREEN_400 if bal >= 0 else ft.Colors.RED_400
            
            if self.total_card.page: self.total_card.update()
            if self.balance_card.page: self.balance_card.update()
        except Exception as e:
            print(f"Erro update stats: {e}")

    def update_ticker(self):
        """Reconstroi a linha de cotações com as moedas"""
        self.rates_row.controls = []
        
        # Tenta pegar do RATES_DISPLAY (formato rico) ou RATES (formato simples)
        rates_display = getattr(FinanceService, 'RATES_DISPLAY', {})
        rates_simple = getattr(FinanceService, 'RATES', {})

        # Lista de moedas que queremos mostrar
        targets = ["USD", "ARS", "PYG"]
        
        if not rates_display and not rates_simple:
            self.rates_row.controls.append(ft.Text("Carregando taxas...", size=10, color=ft.Colors.GREY))
        else:
            for code in targets:
                # Tenta pegar dados ricos
                data = rates_display.get(code)
                
                # Se não tiver rico, monta básico com o simples
                if not data:
                    val = rates_simple.get(code, 0)
                    if code == 'BLUE': val = rates_simple.get('BLUE', 0)
                    flag = "💵"
                else:
                    val = data['val']
                    flag = data['flag']

                if val > 0:
                    # Formatação específica por moeda
                    if code == "USD": txt = f"R$ {val:.2f}"
                    elif code == "ARS": txt = f"R$ 1 = ${val:.0f}" # Ex: 1 Real = 170 Pesos
                    elif code == "PYG": txt = f"R$ 1 = ₲ {val:.0f}"
                    else: txt = str(val)

                    card = ft.Container(
                        bgcolor=ft.Colors.BLACK45, 
                        padding=ft.padding.symmetric(horizontal=12, vertical=8), 
                        border_radius=15,
                        border=ft.border.all(1, ft.Colors.WHITE10),
                        content=ft.Row([
                            ft.Text(flag, size=14), 
                            ft.Text(code, size=11, weight="bold", color=ft.Colors.GREY_400), 
                            ft.Text(txt, size=12, weight="bold", color=ft.Colors.WHITE)
                        ], spacing=6, alignment="center")
                    )
                    self.rates_row.controls.append(card)

        if self.rates_row.page:
            self.rates_row.update()