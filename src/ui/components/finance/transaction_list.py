import flet as ft
from src.logic.finance_service import FinanceService

class TransactionList(ft.Column):
    def __init__(self, page: ft.Page, user, profiles, on_edit_click=None, on_update_callback=None):
        super().__init__(expand=True, scroll=ft.ScrollMode.HIDDEN, spacing=8)
        self.main_page = page
        self.user = user
        self.profiles = profiles
        self.on_edit_click = on_edit_click
        self.on_update_callback = on_update_callback

    def render(self, transactions):
        self.controls = []
        if not transactions:
            self.controls.append(ft.Container(content=ft.Text("Nenhum registro.", color=ft.Colors.GREY_700), alignment=ft.Alignment(0,0), padding=30))
        else:
            for tx in transactions:
                self.controls.append(self._create_tx_card(tx))
        if self.page: self.update()

    def _get_profile_name(self, uid):
        return next((p["name"] for p in self.profiles if str(p["id"]) == str(uid)), "Alguém")

    def _create_tx_card(self, tx):
        my_id = str(self.user["id"])
        is_payer = str(tx["payer_id"]) == my_id
        
        # --- ESTILO ELEGANTE (FAIXA LATERAL) ---
        if is_payer:
            # Crédito (Eu paguei) -> Faixa Verde
            strip_color = ft.Colors.GREEN_500
            val_color = ft.Colors.GREEN_200
            role_text = "Você pagou"
        else:
            # Débito (Me incluíram) -> Faixa Vermelha
            strip_color = ft.Colors.RED_500
            val_color = ft.Colors.RED_200
            role_text = f"Pago por {tx['payer_name']}"

        # Contestação
        contested_list = [str(x) for x in tx.get("contested_by", [])]
        is_contested_anyone = len(contested_list) > 0
        i_contested = my_id in contested_list
        
        # Se contestado, a faixa vira Laranja para chamar atenção
        if is_contested_anyone:
            strip_color = ft.Colors.ORANGE_500
            
        # Ações
        actions = []
        if is_payer:
            actions.extend([
                ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE_GREY_400, icon_size=18, tooltip="Editar", on_click=lambda e: self.on_edit_click(tx)),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.GREY_600, icon_size=18, tooltip="Apagar", on_click=lambda e: self.main_page.run_task(self._delete_tx, tx["id"]))
            ])
        else:
            icon = ft.Icons.FLAG if i_contested else ft.Icons.FLAG_OUTLINED
            col = ft.Colors.ORANGE if i_contested else ft.Colors.GREY_600
            actions.append(ft.IconButton(icon, icon_color=col, icon_size=18, tooltip="Sinalizar", on_click=lambda e: self.main_page.run_task(self._toggle_contest, tx["id"])))

        # Header de Contestação (Texto pequeno acima)
        header = ft.Container()
        if is_contested_anyone:
            names = [self._get_profile_name(uid) for uid in contested_list]
            header = ft.Text(f"⚠ Sinalizado por: {', '.join(names)}", size=10, color=ft.Colors.ORANGE, weight="bold")

        # Formatação Valor
        try: val = float(tx['amount']); val_brl = float(tx.get('amount_brl', 0))
        except: val=0; val_brl=0
        curr_fmt = f"{tx['currency']} {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return ft.Container(
            bgcolor=ft.Colors.GREY_900, # Fundo neutro elegante
            border_radius=5,
            # AQUI ESTÁ A FAIXA LATERAL:
            border=ft.border.only(left=ft.BorderSide(4, strip_color)),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Column([
                header,
                ft.Row([
                    ft.Column([
                        ft.Text(tx["description"], weight="bold", size=15),
                        ft.Text(f"{role_text} • {tx['date']}", size=11, color=ft.Colors.GREY_500)
                    ], expand=True, spacing=2),
                    
                    ft.Column([
                        ft.Text(curr_fmt, weight="bold", size=14, color=val_color, text_align="right"),
                        ft.Row(actions, spacing=0, alignment="end")
                    ], spacing=0, alignment="end")
                ], alignment="spaceBetween")
            ])
        )

    async def _delete_tx(self, tx_id):
        await FinanceService.delete_expense(tx_id)
        if self.on_update_callback: await self.on_update_callback()

    async def _toggle_contest(self, tx_id):
        await FinanceService.toggle_contest(tx_id, self.user["id"])
        if self.on_update_callback: await self.on_update_callback()