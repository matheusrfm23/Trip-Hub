import flet as ft

class BaggageDialogManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.bs_content = ft.Container(padding=20)
        self.bs = ft.BottomSheet(
            content=self.bs_content,
            bgcolor=ft.Colors.GREY_900,
            on_dismiss=self._on_dismiss
        )

    def show(self, e):
        self._build_layout()
        if self.bs not in self.page.overlay:
            self.page.overlay.append(self.bs)
        self.bs.open = True
        self.page.update()

    def _on_dismiss(self, e):
        self.bs.open = False
        self.page.update()

    def _build_layout(self):
        # --- Componente Visual de Dimensões ---
        def visual_box(label, w, h, d, color, max_weight):
            return ft.Container(
                bgcolor=ft.Colors.with_opacity(0.1, color),
                border=ft.border.all(2, color),
                border_radius=8,
                padding=10,
                width=160,
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK, size=40, color=color),
                    ft.Text(label, weight="bold", color=color, size=13),
                    ft.Text(f"Até {max_weight}", size=12, weight="bold", color=ft.Colors.WHITE),
                    ft.Container(
                        bgcolor=ft.Colors.BLACK54, padding=5, border_radius=4,
                        content=ft.Column([
                            ft.Text(f"Alt: {h} cm", size=10, color=ft.Colors.WHITE70),
                            ft.Text(f"Larg: {w} cm", size=10, color=ft.Colors.WHITE70),
                            ft.Text(f"Prof: {d} cm", size=10, color=ft.Colors.WHITE70),
                        ], spacing=0)
                    )
                ], alignment="center", horizontal_alignment="center", spacing=2)
            )

        # --- ABA 1: DIMENSÕES (A Bordo) ---
        content_dims = ft.Column([
            ft.Text("O que você PODE levar a bordo:", size=16, weight="bold", color=ft.Colors.GREEN),
            ft.Row([
                visual_box("Item Pessoal", 43, 32, 22, ft.Colors.ORANGE, "10 kg"),
                visual_box("Mala Pequena", 35, 55, 25, ft.Colors.CYAN, "12 kg"),
            ], alignment="center", spacing=15),
            
            ft.Divider(height=20, color=ft.Colors.GREY_800),
            
            ft.Text("1. Item Pessoal (Abaixo do Assento)", weight="bold", color=ft.Colors.ORANGE),
            ft.Text("• Bolsa, mochila, pasta de notebook.", size=13),
            ft.Text("• Deve caber embaixo da poltrona à frente.", size=13),
            
            ft.Container(height=10),
            
            ft.Text("2. Mala Pequena (Compartimento Superior)", weight="bold", color=ft.Colors.CYAN),
            ft.Text("• Deve incluir as rodinhas nas medidas.", size=13),
            ft.Text("• Se faltar espaço, poderá ser despachada no portão (gratuitamente).", size=13, italic=True),
            
            ft.Container(
                bgcolor=ft.Colors.RED_900, padding=10, border_radius=8, margin=ft.margin.only(top=10),
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.WHITE), 
                    ft.Text("Atenção: Tarifa Light NÃO inclui bagagem despachada!", size=12, weight="bold", expand=True)
                ])
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # --- ABA 2: LÍQUIDOS & HIGIENE ---
        content_liquids = ft.Column([
            ft.Text("Higiene Pessoal & Líquidos", weight="bold", size=16, color=ft.Colors.BLUE_200),
            
            ft.Text("✅ Permitido:", weight="bold", color=ft.Colors.GREEN),
            ft.Text("• Álcool em gel, Perfumes, Desodorantes, Shampoo."),
            ft.Text("• Atomizadores e Medicamentos com álcool."),
            ft.Text("• Removedor de Esmalte (Sem acetona)."),
            
            ft.Divider(),
            
            ft.Text("⚠️ Regras de Quantidade:", weight="bold", color=ft.Colors.AMBER),
            ft.Text("• Máximo 4 frascos de aerossol por pessoa."),
            ft.Text("• Cada frasco: Máx 300ml ou 300g."),
            ft.Text("• Total geral (tudo somado): Máx 2kg ou 2L."),
            
            ft.Divider(),
            
            ft.Text("🚫 Proibido:", weight="bold", color=ft.Colors.RED),
            ft.Text("• Acetona pura."),
            ft.Text("• Alvejantes ou Cloro."),
            
            ft.Divider(),
            ft.Text("🍷 Bebidas Alcoólicas (Maiores de 18):", weight="bold"),
            ft.Text("• Até 23% teor: Sem limite (dentro do peso da mala)."),
            ft.Text("• 24% a 70% teor: Máximo 5L por pessoa (frascos < 1L)."),
            ft.Text("• Acima de 70%: PROIBIDO."),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # --- ABA 3: ELETRÔNICOS & BATERIAS ---
        content_elec = ft.Column([
            ft.Text("Eletrônicos & Baterias", weight="bold", size=16, color=ft.Colors.YELLOW),
            ft.Text("Estes itens devem ir NA MÃO. Nunca despache!", italic=True),
            
            ft.Container(height=10),
            
            ft.Text("✅ Permitido (Uso Pessoal):", weight="bold", color=ft.Colors.GREEN),
            ft.Text("• Celular, Notebook, Câmera, Tablet."),
            ft.Text("• Até 15 dispositivos por pessoa."),
            ft.Text("• Até 20 baterias extras (pilhas, power banks)."),
            
            ft.Divider(),
            
            ft.Text("🔋 Regras de Baterias (Lítio/Power Bank):", weight="bold", color=ft.Colors.ORANGE),
            ft.Text("• Devem ir protegidas contra curto-circuito."),
            ft.Text("• Máximo 100Wh ou 12V (Padrão maioria dos power banks)."),
            ft.Text("• Entre 100Wh e 160Wh: Precisa de autorização GOL."),
            ft.Text("• Acima de 160Wh: PROIBIDO."),
            
            ft.Divider(),
            
            ft.Text("🚬 Cigarro Eletrônico / Vape:", weight="bold"),
            ft.Text("• Permitido APENAS na bagagem de mão (Voo Nacional)."),
            ft.Text("• Proibido em voos internacionais."),
            
            ft.Container(height=10),
            ft.Text("🚫 Smart Bags:", weight="bold", color=ft.Colors.RED),
            ft.Text("• Se a bateria não for removível: PROIBIDO."),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # --- ABA 4: PROIBIDOS ---
        content_forbidden = ft.Column([
            ft.Text("PROIBIDO LEVAR A BORDO", weight="bold", size=18, color=ft.Colors.RED),
            ft.Text("Estes itens serão retidos na inspeção (Raio-X).", size=12),
            
            ft.Container(height=10),
            
            ft.Text("🔪 Cortantes e Perfurantes:", weight="bold", color=ft.Colors.RED_200),
            ft.Text("• Facas, Canivetes, Estiletes."),
            ft.Text("• Tesouras grandes (lâmina > 6cm)."),
            ft.Text("• Alicates grandes."),
            
            ft.Container(height=10),
            
            ft.Text("🛠️ Ferramentas:", weight="bold", color=ft.Colors.RED_200),
            ft.Text("• Martelo, Chave de fenda, Pé de cabra."),
            ft.Text("• Furadeiras e brocas."),
            
            ft.Container(height=10),
            
            ft.Text("🔥 Inflamáveis / Explosivos:", weight="bold", color=ft.Colors.RED_200),
            ft.Text("• Fogos de artifício."),
            ft.Text("• Combustíveis (gás, fluido de isqueiro)."),
            ft.Text("• Spray de Pimenta (Totalmente proibido)."),
            
            ft.Container(height=10),
            ft.Text("💡 Dica:", weight="bold", color=ft.Colors.GREEN),
            ft.Text("Se tiver dúvida, não leve. Como não temos bagagem despachada, o item será jogado fora no aeroporto."),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # --- Menu de Navegação ---
        content_area = ft.Container(content=content_dims, expand=True) # Default

        menu_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)

        def switch(e, content, btn):
            content_area.content = content
            content_area.update()
            for b in menu_row.controls: b.icon_color = ft.Colors.GREY
            btn.icon_color = ft.Colors.CYAN
            menu_row.update()

        btn1 = ft.IconButton(ft.Icons.BACKPACK, tooltip="Dimensões", icon_color=ft.Colors.CYAN)
        btn1.on_click = lambda e: switch(e, content_dims, btn1)
        
        btn2 = ft.IconButton(ft.Icons.WATER_DROP, tooltip="Líquidos", icon_color=ft.Colors.GREY)
        btn2.on_click = lambda e: switch(e, content_liquids, btn2)
        
        btn3 = ft.IconButton(ft.Icons.BATTERY_CHARGING_FULL, tooltip="Eletrônicos", icon_color=ft.Colors.GREY)
        btn3.on_click = lambda e: switch(e, content_elec, btn3)

        btn4 = ft.IconButton(ft.Icons.BLOCK, tooltip="Proibidos", icon_color=ft.Colors.GREY)
        btn4.on_click = lambda e: switch(e, content_forbidden, btn4)

        menu_row.controls = [btn1, btn2, btn3, btn4]

        # Montagem do BottomSheet (Ocupa 80% da tela para caber tudo)
        h = self.page.height if self.page.height else 800
        self.bs_content.height = h * 0.70
        self.bs_content.content = ft.Column([
            ft.Container(width=40, height=4, bgcolor=ft.Colors.GREY_600, border_radius=2, alignment=ft.Alignment(0,0), margin=ft.margin.only(bottom=10)),
            ft.Text("Guia Oficial - Bagagem de Mão", size=18, weight="bold", text_align="center"),
            menu_row,
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            ft.Container(height=10),
            content_area
        ])