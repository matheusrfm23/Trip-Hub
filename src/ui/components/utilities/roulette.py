# ARQUIVO: src/ui/components/utilities/roulette.py
import flet as ft
import random
import asyncio

class PlaceRoulette(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=False)
        self.page_ref = page
        self.items = [] # Lista de candidatos
        self.is_spinning = False

        # --- ESTILOS ---
        self.card_bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        self.border_color = ft.Colors.WHITE10
        
        # Gradiente com coordenadas numéricas (Blindado)
        self.highlight_gradient = ft.LinearGradient(
            colors=[ft.Colors.PURPLE_900, ft.Colors.DEEP_PURPLE_900],
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1)
        )

        # --- 1. INPUT DE OPÇÕES ---
        self.tf_manual_input = ft.TextField(
            label="Adicionar Opção",
            hint_text="Ex: Pizza, Quem Paga, McDonalds...",
            expand=True,
            bgcolor=ft.Colors.BLACK26,
            border_radius=10,
            on_submit=self._add_manual_item
        )
        
        self.btn_add = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE, 
            icon_color=ft.Colors.GREEN_400,
            icon_size=30,
            on_click=self._add_manual_item
        )
        
        self.input_row = ft.Row(
            controls=[self.tf_manual_input, self.btn_add],
            alignment=ft.MainAxisAlignment.CENTER
        )

        # --- 2. LISTA DE CANDIDATOS ---
        self.chip_list = ft.Row(wrap=True, spacing=5)
        self.txt_count = ft.Text("0 opções adicionadas", size=12, color=ft.Colors.GREY)

        container_lista = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.LIST, size=12, color=ft.Colors.GREY), self.txt_count]),
                self.chip_list
            ]),
            padding=10,
            bgcolor=ft.Colors.BLACK12,
            border_radius=8
        )

        # --- 3. O DISPLAY DA ROLETA ---
        self.display_text = ft.Text(
            "Adicione opções...", 
            size=24, 
            weight="bold", 
            color=ft.Colors.WHITE24,
            text_align="center"
        )
        
        self.display_container = ft.Container(
            content=self.display_text,
            alignment=ft.Alignment(0, 0), # Coordenada numérica
            padding=30,
            border_radius=20,
            gradient=ft.LinearGradient(colors=[ft.Colors.BLACK87, ft.Colors.BLACK]),
            border=ft.border.all(2, ft.Colors.PURPLE_900),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.PURPLE_900),
            animate=ft.Animation(300, ft.AnimationCurve.BOUNCE_OUT) 
        )

        # --- 4. BOTÃO DE GIRAR ---
        self.btn_spin = ft.Container(
            gradient=ft.LinearGradient(
                colors=[ft.Colors.PINK_600, ft.Colors.PURPLE_700],
                begin=ft.Alignment(-1, -1), 
                end=ft.Alignment(1, 1)
            ),
            border_radius=30,
            padding=5,
            on_click=self._spin_roulette,
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CASINO, color=ft.Colors.WHITE),
                    ft.Text("GIRAR AGORA", weight="bold", size=16)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                width=200, height=50
            )
        )

        # --- CONTEÚDO PRINCIPAL (Oculto até expandir) ---
        self.main_content = ft.Column(
            controls=[
                self.input_row,
                ft.Container(height=5),
                container_lista,
                ft.Divider(color=ft.Colors.WHITE10, height=20),
                self.display_container,
                ft.Container(height=20),
                # CORREÇÃO AQUI: ft.Alignment(0, 0) em vez de ft.alignment.center
                ft.Container(content=self.btn_spin, alignment=ft.Alignment(0, 0))
            ]
        )

        # --- ESTRUTURA RECOLHÍVEL (ExpansionTile) ---
        self.master_tile = ft.ExpansionTile(
            title=ft.Text("Roleta de Decisões", size=16, weight="bold", color=ft.Colors.WHITE),
            subtitle=ft.Text("Sorteie locais, pratos ou quem paga a conta", size=12, color=ft.Colors.PURPLE_200),
            leading=ft.Icon(ft.Icons.TOYS, color=ft.Colors.PURPLE_400),
            bgcolor=ft.Colors.GREY_900,
            controls=[
                ft.Container(
                    padding=20,
                    content=self.main_content
                )
            ]
        )

        # Container externo com borda (padrão do App)
        self.controls = [
            ft.Container(
                border_radius=15,
                border=ft.border.all(1, ft.Colors.GREY_800),
                content=self.master_tile
            )
        ]

    def _update_count(self):
        qtd = len(self.items)
        self.txt_count.value = f"{qtd} opções adicionadas"
        
        # Atualiza o texto do display se estiver vazio
        if qtd == 0:
            self.display_text.value = "Adicione opções..."
            self.display_text.color = ft.Colors.WHITE24
        elif not self.is_spinning and self.display_text.value == "Adicione opções...":
            self.display_text.value = "Pronto para girar!"
            self.display_text.color = ft.Colors.WHITE
            
        self.update()

    def _add_manual_item(self, e):
        val = self.tf_manual_input.value
        if val:
            self.items.append(val)
            self.chip_list.controls.append(
                ft.Chip(
                    label=ft.Text(val), 
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    on_delete=self._remove_item,
                    data=val
                )
            )
            self.tf_manual_input.value = ""
            self.tf_manual_input.focus()
            self._update_count()
            self.update()

    def _remove_item(self, e):
        val = e.control.data
        if val in self.items:
            self.items.remove(val)
            self.chip_list.controls.remove(e.control)
            self._update_count()
            self.update()

    async def _spin_roulette(self, e):
        if not self.items:
            self.tf_manual_input.error_text = "Adicione algo primeiro!"
            self.tf_manual_input.update()
            return
        
        self.tf_manual_input.error_text = None

        if self.is_spinning: return
        self.is_spinning = True
        
        # Reset visual
        self.display_container.border = ft.border.all(2, ft.Colors.PURPLE_900)
        self.display_container.gradient = ft.LinearGradient(colors=[ft.Colors.BLACK87, ft.Colors.BLACK])
        self.btn_spin.opacity = 0.5
        self.display_text.color = ft.Colors.WHITE
        self.update()

        # --- ANIMAÇÃO ---
        loops = 30 
        delay = 0.05 
        
        for i in range(loops):
            current_choice = random.choice(self.items)
            self.display_text.value = current_choice
            
            # Pulso
            self.display_container.scale = 1.05
            self.update()
            await asyncio.sleep(0.05)
            self.display_container.scale = 1.0
            self.update()

            # Desaceleração
            if i > loops - 10:
                delay += 0.05 
            
            await asyncio.sleep(delay)

        # --- VENCEDOR ---
        winner = random.choice(self.items)
        self.display_text.value = winner
        self.display_text.color = ft.Colors.YELLOW_400
        self.display_text.size = 30
        
        # Estilo de Vitória
        self.display_container.gradient = ft.LinearGradient(
            colors=[ft.Colors.GREEN_900, ft.Colors.BLACK],
            begin=ft.Alignment(-1, -1), 
            end=ft.Alignment(1, 1)
        )
        self.display_container.border = ft.border.all(4, ft.Colors.GREEN_400)
        self.display_container.scale = 1.1
        self.display_container.shadow = ft.BoxShadow(blur_radius=30, color=ft.Colors.GREEN_600)
        
        self.is_spinning = False
        self.btn_spin.opacity = 1.0
        self.update()
        
        await asyncio.sleep(2)
        # Retorna ao tamanho normal, mas mantém o vencedor
        self.display_container.scale = 1.0
        self.display_text.size = 26
        self.update()