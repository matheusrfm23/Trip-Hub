# ARQUIVO: src/ui/components/utilities/checklist_panel.py
import flet as ft
import uuid
from src.logic.checklist_service import ChecklistService

class ChecklistPanel(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_ref = page
        self.user_id = self.page_ref.user_profile["id"]
        self.items = []
        
        # --- ESTILOS DO CARD (Preto por fora) ---
        self.border_radius = 15
        self.bgcolor = ft.Colors.BLACK 
        self.border = ft.border.all(1, ft.Colors.WHITE10)
        self.padding = 0 
        
        # --- ELEMENTOS INTERNOS ---
        self.progress_bar = ft.ProgressBar(value=0, color=ft.Colors.GREEN_400, bgcolor=ft.Colors.BLACK45, height=6)
        self.txt_status = ft.Text("0% Concluído", size=12, color=ft.Colors.GREY)
        
        # Coluna de itens
        self.list_view = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)
        
        # Input de Adicionar
        self.tf_new_item = ft.TextField(
            hint_text="Adicionar item (Ex: Chapinha, Carregador...)", 
            expand=True, 
            height=40,
            text_size=14,
            content_padding=10,
            bgcolor=ft.Colors.BLACK54, 
            border_radius=8,
            on_submit=self._add_item
        )

        # --- CONTEÚDO EXPANDIDO (Com Fundo Cinza) ---
        self.expanded_content = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE), # Cinza apenas ao abrir
            padding=20,
            border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
            content=ft.Column([
                # Barra de Progresso
                ft.Row([ft.Text("Progresso:", size=12, color=ft.Colors.GREY), self.txt_status], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.progress_bar,
                ft.Container(height=15),
                
                # Área de Inserção
                ft.Row([
                    self.tf_new_item,
                    ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN_400, on_click=self._add_item)
                ]),
                
                ft.Divider(color=ft.Colors.WHITE10),
                
                # Lista de Itens
                ft.Container(
                    content=self.list_view,
                    height=250, 
                    padding=5,
                    border_radius=8,
                    bgcolor=ft.Colors.BLACK26, 
                ),
                
                ft.Container(height=10),
                
                # Botão de Reset
                ft.Row([
                    ft.TextButton(
                        "Limpar Marcações (Nova Viagem)", 
                        icon=ft.Icons.REFRESH, 
                        icon_color=ft.Colors.GREY_500,
                        style=ft.ButtonStyle(color=ft.Colors.GREY_500),
                        on_click=self._reset_list
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ])
        )

        # --- ESTRUTURA PRINCIPAL (ExpansionTile) ---
        self.expansion_tile = ft.ExpansionTile(
            title=ft.Text("Checklist de Bagagem", size=16, weight="bold", color=ft.Colors.WHITE),
            subtitle=ft.Text("Lista pessoal de itens para não esquecer", size=12, color=ft.Colors.GREY_400),
            leading=ft.Icon(ft.Icons.CHECKLIST, color=ft.Colors.CYAN),
            bgcolor=ft.Colors.TRANSPARENT,
            controls=[self.expanded_content],
            shape=ft.RoundedRectangleBorder(radius=15),
            collapsed_shape=ft.RoundedRectangleBorder(radius=15),
            tile_padding=ft.padding.symmetric(horizontal=10, vertical=5)
        )

        self.content = self.expansion_tile

    def did_mount(self):
        self._load_items()

    def _load_items(self):
        self.items = ChecklistService.get_checklist(self.user_id)
        self._render_list()

    def _render_list(self):
        self.list_view.controls = []
        total = len(self.items)
        checked_count = 0

        # Ordena: Não marcados primeiro
        sorted_items = sorted(self.items, key=lambda x: x.get("checked", False))

        for item in sorted_items:
            is_checked = item.get("checked", False)
            if is_checked: checked_count += 1

            text_style = ft.TextStyle(
                decoration=ft.TextDecoration.LINE_THROUGH if is_checked else None,
                color=ft.Colors.GREY if is_checked else ft.Colors.WHITE
            )

            checkbox = ft.Checkbox(
                label=item["text"],
                value=is_checked,
                label_style=text_style,
                active_color=ft.Colors.CYAN,
                check_color=ft.Colors.BLACK,
                on_change=lambda e, i=item: self._toggle_item(e, i)
            )

            delete_btn = ft.IconButton(
                ft.Icons.CLOSE, 
                icon_color=ft.Colors.RED_900 if is_checked else ft.Colors.RED_400, 
                icon_size=16,
                tooltip="Remover item",
                on_click=lambda e, i=item: self._delete_item(i)
            )

            row = ft.Container(
                bgcolor=ft.Colors.TRANSPARENT,
                padding=2,
                content=ft.Row([
                    ft.Container(content=checkbox, expand=True),
                    delete_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
            self.list_view.controls.append(row)

        if not self.items:
            self.list_view.controls.append(
                ft.Text("Nenhum item adicionado ainda.", italic=True, color=ft.Colors.GREY, size=12, text_align="center")
            )

        progress = checked_count / total if total > 0 else 0
        self.progress_bar.value = progress
        self.txt_status.value = f"{int(progress * 100)}%"
        self.update()

    def _toggle_item(self, e, item):
        item["checked"] = e.control.value
        ChecklistService.save_checklist(self.user_id, self.items)
        self._render_list()

    async def _add_item(self, e):
        text = self.tf_new_item.value
        if text:
            new_item = {
                "id": str(uuid.uuid4()),
                "text": text,
                "checked": False
            }
            self.items.insert(0, new_item)
            ChecklistService.save_checklist(self.user_id, self.items)
            self.tf_new_item.value = ""
            self._render_list()
            
            try:
                await self.tf_new_item.focus()
            except:
                pass 

    def _delete_item(self, item):
        self.items.remove(item)
        ChecklistService.save_checklist(self.user_id, self.items)
        self._render_list()

    def _reset_list(self, e):
        self.items = ChecklistService.reset_checks(self.user_id)
        self._render_list()
        
        # CORREÇÃO: Método compatível de SnackBar
        snack = ft.SnackBar(content=ft.Text("Checklist limpo para nova viagem!"))
        self.page_ref.snack_bar = snack
        snack.open = True
        self.page_ref.update()