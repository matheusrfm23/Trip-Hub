# ARQUIVO: src/ui/components/finance/debts.py
# CHANGE LOG:
# - Abortagem agressiva (early return) se a página já foi destruída na navegação.
# - Proteção em todos os updates assíncronos.

import flet as ft
from src.logic.finance_service import FinanceService

class DebtManager:
    def __init__(self, page: ft.Page, user, profiles):
        self.page = page
        self.user = user
        self.profiles = profiles
        self.selected_contact_id = None
        
        self.debt_carousel = ft.Row(scroll=ft.ScrollMode.HIDDEN, spacing=15) 
        self.debt_detail_list = ft.Column(spacing=10) 
        self.debt_detail_title = ft.Text("Selecione um contato para ver o histórico", size=13, color=ft.Colors.GREY_500, italic=True)
        
        self.container = ft.Column(
            visible=False, expand=True, scroll=ft.ScrollMode.HIDDEN,
            controls=[
                ft.Text("Carteira de Contatos", size=16, weight="bold", color=ft.Colors.CYAN_200),
                ft.Container(content=self.debt_carousel, height=140, padding=ft.padding.only(bottom=10)),
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                ft.Container(height=10),
                self.debt_detail_title, 
                self.debt_detail_list,
                ft.Container(height=80) 
            ]
        )

    def _is_active(self):
        """Verifica de forma segura se o componente ainda existe na tela."""
        return bool(self.container.page and self.debt_carousel.page)

    def _get_profile_name(self, uid):
        return next((p["name"] for p in self.profiles if str(p["id"]) == str(uid)), "Desconhecido")

    async def render_carousel(self):
        if not self._is_active(): return
        
        try:
            contacts = await FinanceService.get_debt_contacts(self.user["id"])
            if not self._is_active(): return # Dupla checagem após await (A rota pode ter mudado durante a API)

            self.debt_carousel.controls = []
            if not contacts:
                self.debt_carousel.controls.append(ft.Container(content=ft.Text("Nenhuma pendência.", color=ft.Colors.GREY_600), padding=20))
            else:
                for c in contacts:
                    c['name'] = self._get_profile_name(c.get("id"))
                    self.debt_carousel.controls.append(self._build_contact_card(c))

            if self._is_active():
                self.debt_carousel.update()
                if self.selected_contact_id: await self._refresh_history()
        except Exception as e:
            pass

    async def _refresh_history(self):
        if not self._is_active(): return
        c_name = self._get_profile_name(self.selected_contact_id)
        await self._load_history(self.selected_contact_id, c_name)

    def _build_contact_card(self, c):
        uid = str(c["id"]); bal = c["balance"]; name = c["name"]; initials = name[:2].upper()
        if bal > 0.01: color = ft.Colors.GREEN_400; txt = f"+{bal:.0f}"; border = ft.Colors.GREEN_900
        elif bal < -0.01: color = ft.Colors.RED_400; txt = f"{bal:.0f}"; border = ft.Colors.RED_900
        else: color = ft.Colors.GREY_400; txt = "0"; border = ft.Colors.GREY_800
        
        is_sel = str(self.selected_contact_id) == uid
        
        return ft.Container(
            opacity=1.0 if is_sel or self.selected_contact_id is None else 0.5,
            on_click=lambda e: self.page.run_task(self._select_contact, uid, name) if self._is_active() else None,
            content=ft.Column([
                ft.Container(width=60, height=60, border_radius=30, bgcolor=ft.Colors.GREY_900, border=ft.border.all(3 if is_sel else 2, ft.Colors.CYAN if is_sel else border), alignment=ft.Alignment(0,0), content=ft.Text(initials, size=18, weight="bold", color=ft.Colors.WHITE)),
                ft.Text(name.split()[0], size=12, weight="bold"),
                ft.Text(f"R$ {txt}", size=12, color=color, weight="bold")
            ], spacing=5, horizontal_alignment="center")
        )

    async def _select_contact(self, contact_id, contact_name):
        if not self._is_active(): return
        self.selected_contact_id = contact_id
        await self.render_carousel() 
        await self._load_history(contact_id, contact_name)

    async def _load_history(self, contact_id, contact_name):
        if not self._is_active(): return
        
        self.debt_detail_title.value = f"Extrato com {contact_name}"
        try:
            self.debt_detail_title.update()
        except: pass
        
        try:
            history = await FinanceService.get_pairwise_history(self.user["id"], contact_id)
            if not self._is_active(): return

            self.debt_detail_list.controls = []
            if not history: self.debt_detail_list.controls.append(ft.Text("Vazio.", italic=True))
            for item in history: self.debt_detail_list.controls.append(self._build_history_card(item))
            
            if self._is_active(): 
                self.debt_detail_list.update()
        except Exception: pass

    def _build_history_card(self, item):
        is_credit = item.get("type") == "credit"
        
        if is_credit: strip_col = ft.Colors.GREEN_600; val_col = ft.Colors.GREEN_200
        else: strip_col = ft.Colors.RED_600; val_col = ft.Colors.RED_200

        contested = [str(x) for x in item.get("contested_by", [])]
        if contested: strip_col = ft.Colors.ORANGE_500 

        actions = []
        tx_id = item.get("id")
        my_id = str(self.user["id"])

        if tx_id:
            if is_credit: 
                actions.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.GREY_600, tooltip="Apagar", icon_size=20, on_click=lambda e: self.page.run_task(self._delete, tx_id) if self._is_active() else None))
            else:
                icon = ft.Icons.FLAG if my_id in contested else ft.Icons.FLAG_OUTLINED
                col = ft.Colors.ORANGE if my_id in contested else ft.Colors.GREY_600
                actions.append(ft.IconButton(icon, icon_color=col, tooltip="Sinalizar", icon_size=20, on_click=lambda e: self.page.run_task(self._contest, tx_id) if self._is_active() else None))

        return ft.Container(
            bgcolor=ft.Colors.GREY_900, 
            border_radius=5,
            border=ft.border.only(left=ft.BorderSide(4, strip_col)), 
            padding=12,
            content=ft.Row([
                ft.Column([
                    ft.Text(item.get("desc", ""), weight="bold", size=14),
                    ft.Text(f"{item.get('date', '')}", size=11, color=ft.Colors.GREY_500),
                    ft.Text("⚠ Contestação" if contested else "", size=10, color=ft.Colors.ORANGE)
                ], expand=True, spacing=2),
                ft.Column([
                    ft.Text(f"R$ {item.get('split_brl', 0):.2f}", weight="bold", size=14, color=val_col, text_align="right"),
                    ft.Row(actions, spacing=0, alignment="end")
                ], spacing=0, alignment="end")
            ], alignment="spaceBetween")
        )

    async def _delete(self, tx_id):
        await FinanceService.delete_expense(tx_id)
        await self.render_carousel() 

    async def _contest(self, tx_id):
        await FinanceService.toggle_contest(tx_id, self.user["id"])
        if self.selected_contact_id: await self._refresh_history()