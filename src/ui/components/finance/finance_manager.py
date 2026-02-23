import flet as ft
from src.logic.finance_service import FinanceService
from src.logic.auth_service import AuthService

from src.ui.components.finance.split_bill import SplitBillCard
from src.ui.components.finance.converter import ConverterCard
from src.ui.components.finance.dashboard import FinanceDashboard
from src.ui.components.finance.debts import DebtManager
from src.ui.components.finance.transaction_list import TransactionList
from src.ui.components.finance.expense_dialog import ExpenseDialog

class FinanceManager(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.user = getattr(self.main_page, 'user_profile', None)
        self.profiles = []
        
        self.split_card = SplitBillCard()
        self.conv_card = ConverterCard()
        self.dashboard = FinanceDashboard() # Aqui está o Ticker
        
        self.debt_manager = None 
        self.tx_list = None
        self.dialog_manager = None
        
        self.loading = ft.ProgressBar(width=100, color=ft.Colors.CYAN, visible=False)
        self.btn_extrato = ft.ElevatedButton("Extrato", icon=ft.Icons.LIST, bgcolor=ft.Colors.CYAN_900, color=ft.Colors.WHITE, expand=True, on_click=lambda e: self._switch_view("extrato"))
        self.btn_radar = ft.ElevatedButton("Dívidas", icon=ft.Icons.RADAR, bgcolor=ft.Colors.GREY_800, color=ft.Colors.GREY, expand=True, on_click=lambda e: self._switch_view("radar"))
        
        self.view_container = ft.Container(expand=True) 

        self.controls = [
            ft.Stack(expand=True, controls=[
                ft.Column(scroll=ft.ScrollMode.HIDDEN, expand=True, controls=[
                    ft.Container(padding=15, content=ft.Column([
                        ft.Container(self.loading, height=5),
                        
                        # 1. Divisão
                        self.split_card, ft.Container(height=5),
                        
                        # 2. MOEDAS (TICKER) - Restaurado
                        self.dashboard.rates_row, ft.Container(height=5),
                        
                        # 3. Conversor
                        self.conv_card, ft.Container(height=10),
                        
                        # 4. Totais
                        ft.Row([self.dashboard.total_card, self.dashboard.balance_card], spacing=10), ft.Container(height=10),
                        
                        # 5. Navegação
                        ft.Row([self.btn_extrato, self.btn_radar], spacing=5),
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        self.view_container,
                        ft.Container(height=80)
                    ]))
                ]),
                ft.Container(right=20, bottom=20, content=ft.FloatingActionButton(
                    icon=ft.Icons.ADD, bgcolor=ft.Colors.CYAN, 
                    on_click=lambda e: self.dialog_manager.open() if self.dialog_manager else None
                ))
            ])
        ]

    def did_mount(self):
        self.load_data()

    def load_data(self):
        if hasattr(self.main_page, 'user_profile'): self.user = self.main_page.user_profile
        if self.loading.page: self.loading.visible = True; self.loading.update()
        self.main_page.run_task(self._init_async)

    async def _init_async(self):
        try:
            # Busca taxas na API
            await FinanceService.update_rates()
            
            # [CRUCIAL] Atualiza o visual das moedas agora que temos dados
            if self.dashboard.rates_row.page:
                self.dashboard.update_ticker()

            self.profiles = await AuthService.get_profiles()
            
            if not self.tx_list:
                self.tx_list = TransactionList(self.main_page, self.user, self.profiles, 
                                               on_edit_click=lambda tx: self.dialog_manager.open(tx),
                                               on_update_callback=self._refresh_all)
                self.view_container.content = self.tx_list
            else:
                self.tx_list.user = self.user

            if self.view_container.page: self.view_container.update()

            if not self.dialog_manager:
                self.dialog_manager = ExpenseDialog(self.main_page, self.user, self.profiles, on_save_callback=self._refresh_all)
            else:
                self.dialog_manager.user = self.user; self.dialog_manager.profiles = self.profiles

            if not self.debt_manager:
                self.debt_manager = DebtManager(self.main_page, self.user, self.profiles)
            else:
                self.debt_manager.user = self.user; self.debt_manager.profiles = self.profiles

            await self._refresh_all()

        except Exception as e:
            print(f"Erro init financeiro: {e}")
        finally:
            if self.loading.page: self.loading.visible = False; self.loading.update()

    async def _refresh_all(self):
        if not self.page: return 
        try:
            report = await FinanceService.get_report(self.user["id"])
            if self.dashboard.total_card.page: self.dashboard.update_stats(report)
            if self.tx_list and self.tx_list.page and self.view_container.content == self.tx_list: 
                self.tx_list.render(report['transactions'])
            if self.debt_manager: await self.debt_manager.render_carousel()
        except Exception as e: 
            if "Control must be added" not in str(e): print(f"Erro refresh: {e}")

    def _switch_view(self, view_name):
        if view_name == "extrato":
            self.view_container.content = self.tx_list
            self.btn_extrato.bgcolor = ft.Colors.CYAN_900; self.btn_extrato.color = ft.Colors.WHITE
            self.btn_radar.bgcolor = ft.Colors.GREY_800; self.btn_radar.color = ft.Colors.GREY
            self.main_page.run_task(self._refresh_all)
        else: 
            if not self.debt_manager: self.debt_manager = DebtManager(self.main_page, self.user, self.profiles)
            self.debt_manager.container.visible = True
            self.view_container.content = self.debt_manager.container
            self.btn_radar.bgcolor = ft.Colors.CYAN_900; self.btn_radar.color = ft.Colors.WHITE
            self.btn_extrato.bgcolor = ft.Colors.GREY_800; self.btn_extrato.color = ft.Colors.GREY
            self.main_page.run_task(self.debt_manager.render_carousel)
        self.update()