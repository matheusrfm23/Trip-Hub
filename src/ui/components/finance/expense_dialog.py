import flet as ft
from src.logic.finance_service import FinanceService

class ExpenseDialog:
    def __init__(self, page: ft.Page, user, profiles, on_save_callback):
        self.page = page
        self.user = user
        self.profiles = profiles
        self.on_save_callback = on_save_callback
        self.editing_id = None
        self.selected_users = set()

        # Componentes
        self.d_amount = ft.TextField(value="0,00", text_style=ft.TextStyle(size=32, weight="bold", color=ft.Colors.CYAN_200),
            text_align="center", border=ft.InputBorder.NONE, keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_money_change, prefix=ft.Text("R$ ", size=20, color=ft.Colors.CYAN_700), height=60)

        self.d_desc = ft.TextField(label="Descrição", hint_text="Ex: Jantar", border_radius=10, filled=True, bgcolor=ft.Colors.BLACK45)
        self.d_curr = ft.Dropdown(label="Moeda", value="BRL", width=100, border_radius=10, filled=True, bgcolor=ft.Colors.BLACK45, options=[ft.dropdown.Option(x) for x in ["BRL", "USD", "ARS", "PYG"]])
        self.d_cat = ft.Dropdown(label="Categoria", value="Alimentação", expand=True, border_radius=10, filled=True, bgcolor=ft.Colors.BLACK45, options=[ft.dropdown.Option(x) for x in ["Alimentação", "Transporte", "Hospedagem", "Lazer", "Compras", "Outros"]])
        self.chips_row = ft.Row(wrap=True, spacing=8)
        self.select_all_btn = ft.TextButton("Todos", on_click=self._toggle_all)

        # Dialog Moderno
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Text("Nova Despesa", weight="bold"), ft.IconButton(ft.Icons.CLOSE, on_click=self._close)], alignment="spaceBetween"),
            content=ft.Container(
                width=400, height=550, # Altura Aumentada
                content=ft.Column([
                    ft.Container(content=self.d_amount, bgcolor=ft.Colors.BLACK26, border_radius=15, padding=10),
                    ft.Container(height=10),
                    ft.Row([self.d_curr, self.d_cat]),
                    self.d_desc,
                    ft.Divider(),
                    ft.Row([ft.Text("Quem consome?", size=12, color=ft.Colors.GREY), self.select_all_btn], alignment="spaceBetween"),
                    ft.Container(content=self.chips_row, padding=10, bgcolor=ft.Colors.BLACK12, border_radius=10, expand=True) 
                ], scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._close),
                ft.ElevatedButton("SALVAR", on_click=self._save_tx, bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _close(self, e=None):
        self.dialog.open = False
        self.page.update()

    def _on_money_change(self, e):
        value = e.control.value
        if not value: return
        raw_digits = "".join(filter(str.isdigit, value))
        if not raw_digits: raw_digits = "0"
        try:
            val_float = int(raw_digits) / 100
            formatted = "{:,.2f}".format(val_float).replace(",", "X").replace(".", ",").replace("X", ".")
            if e.control.value != formatted:
                e.control.value = formatted
                e.control.update()     
        except ValueError: pass 
        
        sym_map = {"BRL": "R$", "USD": "U$", "ARS": "$", "PYG": "₲"}
        curr = self.d_curr.value
        if self.d_amount.prefix and self.d_amount.prefix.value != f"{sym_map.get(curr, '$')} ":
             self.d_amount.prefix.value = f"{sym_map.get(curr, '$')} "
             self.d_amount.update()

    def _update_chips(self):
        self.chips_row.controls = []
        for p in self.profiles:
            pid = str(p["id"])
            is_selected = pid in self.selected_users
            self.chips_row.controls.append(ft.Chip(label=ft.Text(p["name"].split()[0]), leading=ft.Icon(ft.Icons.CHECK if is_selected else ft.Icons.PERSON_OUTLINE), selected=is_selected, selected_color=ft.Colors.CYAN_900, on_select=lambda e, x=pid: self._toggle_user(x), data=pid))
        try:
            if self.chips_row.page: self.chips_row.update()
        except: pass

    def _toggle_user(self, pid):
        if pid in self.selected_users: self.selected_users.remove(pid)
        else: self.selected_users.add(pid)
        self._update_chips()

    def _toggle_all(self, e):
        if len(self.selected_users) == len(self.profiles): self.selected_users.clear()
        else: self.selected_users = {str(p["id"]) for p in self.profiles}
        self._update_chips()

    def open(self, tx_data=None):
        self.editing_id = None; self.selected_users.clear()
        if tx_data:
            self.editing_id = tx_data["id"]; self.d_desc.value = tx_data["description"]; self.d_cat.value = tx_data.get("category", "Outros"); self.d_curr.value = tx_data["currency"]
            self.d_amount.value = f"{tx_data['amount']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.selected_users = {str(uid) for uid in tx_data.get("involved_ids", [])}
            self.dialog.title.controls[0].value = "Editar Despesa"
        else:
            self.d_desc.value = ""; self.d_amount.value = "0,00"; self.d_curr.value = "BRL"; self.d_cat.value = "Alimentação"
            self.selected_users = {str(self.user["id"])}
            self.dialog.title.controls[0].value = "Nova Despesa"
        self._update_chips()
        if self.dialog not in self.page.overlay: self.page.overlay.append(self.dialog)
        self.dialog.open = True; self.page.update()

    async def _save_tx(self, e):
        try: amount = float(self.d_amount.value.replace(".", "").replace(",", "."))
        except: amount = 0.0
        if amount <= 0: self.d_amount.border_color = ft.Colors.RED; self.d_amount.update(); return
        data = {"description": self.d_desc.value or "Sem descrição", "amount": amount, "currency": self.d_curr.value, "category": self.d_cat.value, "payer_id": str(self.user["id"]), "payer_name": self.user["name"], "involved_ids": list(self.selected_users) or [str(self.user["id"])]}
        self.dialog.open = False; self.page.update()
        if self.editing_id: await FinanceService.update_expense(self.editing_id, data)
        else: await FinanceService.add_expense(data)
        if self.on_save_callback: await self.on_save_callback()