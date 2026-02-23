# ARQUIVO: src/ui/components/utilities/tax_calculator.py
import flet as ft
from src.logic.utilities.tax_engine import TaxEngine
from src.logic.finance_service import FinanceService

class TaxCalculator(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=False)
        self.page_ref = page
        
        # --- ESTILOS ---
        self.card_bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        self.border_color = ft.Colors.WHITE10

        # --- 1. Valor da Compra (Formatado) ---
        self.tf_valor = ft.TextField(
            label="Valor da Compra",
            prefix=ft.Text("US$ ", color=ft.Colors.CYAN),
            width=180,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=ft.Colors.BLACK26,
            border_radius=10,
            text_style=ft.TextStyle(size=18, weight="bold", color=ft.Colors.CYAN_100),
            on_change=self._on_value_change, # Formatação ao vivo
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="") # Só aceita números
        )

        # --- 2. Câmbio (Manual ou API) ---
        self.tf_cotacao_manual = ft.TextField(
            label="Cotação Manual",
            prefix=ft.Text("R$ ", color=ft.Colors.GREY),
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=ft.Colors.BLACK26,
            border_radius=10,
            disabled=True,
            text_style=ft.TextStyle(size=14),
            on_change=self._format_currency_live # Formatação ao vivo
        )

        self.rg_cambio = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="api", label="Usar AwesomeAPI"),
                ft.Radio(value="manual", label="Manual"),
            ]),
            value="api",
            on_change=self._mudanca_tipo_cambio
        )

        # --- Container de Cotação Atual ---
        self.txt_cotacao_display = ft.Text("Carregando Câmbio...", size=12, color=ft.Colors.AMBER, weight="bold")

        input_section = ft.Container(
            padding=15,
            bgcolor=self.card_bgcolor,
            border_radius=12,
            border=ft.border.all(1, self.border_color),
            content=ft.Column([
                ft.Text("1. VALORES DA COMPRA", size=12, weight="bold", color=ft.Colors.GREY_500),
                ft.Row([self.tf_valor], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Divider(color=ft.Colors.WHITE10),
                
                ft.Text("Fonte do Câmbio:", size=12, color=ft.Colors.GREY),
                self.rg_cambio, # Radios em linha própria
                
                ft.Container(height=5),
                
                # Linha Híbrida: Status na esquerda, Input na direita
                ft.Row([
                    ft.Container(content=self.txt_cotacao_display, padding=5),
                    self.tf_cotacao_manual
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ])
        )

        # --- 3. Parâmetros de Risco ---
        self.sw_ocultacao = self._criar_switch_risco("Fundo Falso / Ocultação?", ft.Colors.RED)
        self.sw_reincidente = self._criar_switch_risco("Já foi pego (Reincidente)?", ft.Colors.ORANGE)
        self.sw_quantidade = self._criar_switch_risco("Quantidade Comercial (>3)?", ft.Colors.RED)

        risk_section = ft.Container(
            bgcolor=self.card_bgcolor,
            border_radius=12,
            border=ft.border.all(1, self.border_color),
            content=ft.ExpansionTile(
                title=ft.Text("2. Parâmetros de Risco", size=14),
                subtitle=ft.Text("Configure condições especiais", size=12, color=ft.Colors.GREY),
                leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, color=ft.Colors.ORANGE_400),
                controls=[
                    ft.Container(
                        padding=15,
                        content=ft.Column([
                            self.sw_ocultacao,
                            self.sw_reincidente,
                            self.sw_quantidade
                        ])
                    )
                ]
            )
        )

        # --- 4. Botão Calcular ---
        self.btn_calcular = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.CYAN_800, ft.Colors.BLUE_900],
            ),
            border_radius=10,
            padding=2,
            content=ft.ElevatedButton(
                "CALCULAR IMPOSTOS",
                icon=ft.Icons.CALCULATE_OUTLINED,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    bgcolor=ft.Colors.TRANSPARENT,
                    color=ft.Colors.WHITE,
                    elevation=0,
                ),
                height=50,
                width=1000,
                on_click=self._calcular_click
            )
        )

        # --- 5. Resultados ---
        self.results_area = ft.Column(spacing=10)
        
        # Conteúdo Principal
        self.main_content = ft.Column(
            controls=[
                input_section,
                ft.Container(height=5),
                risk_section,
                ft.Container(height=10),
                self.btn_calcular,
                ft.Container(height=10),
                self.results_area
            ]
        )

        # Tile Mestre
        self.master_tile = ft.ExpansionTile(
            title=ft.Text("Calculadora de Importação (2026)", size=16, weight="bold", color=ft.Colors.WHITE),
            subtitle=ft.Text("Simule impostos, multas e compare com RTU", size=12, color=ft.Colors.CYAN_200),
            leading=ft.Icon(ft.Icons.CALCULATE, color=ft.Colors.CYAN),
            bgcolor=ft.Colors.GREY_900,
            controls=[
                ft.Container(
                    padding=15,
                    content=self.main_content
                )
            ]
        )

        self.controls = [
            ft.Container(
                border_radius=15,
                border=ft.border.all(1, ft.Colors.GREY_800),
                content=self.master_tile
            )
        ]

    def did_mount(self):
        """Ao montar o componente, atualiza a cotação automaticamente"""
        self.page_ref.run_task(self._fetch_rates_init)

    async def _fetch_rates_init(self):
        self.txt_cotacao_display.value = "Conectando AwesomeAPI..."
        self.txt_cotacao_display.update()
        
        await FinanceService.update_rates()
        
        # [CORREÇÃO CRÍTICA]
        # Se o usuário saiu da tela enquanto a API respondia, self.page será None.
        # Interrompemos aqui para evitar RuntimeError.
        if not self.page: 
            return

        rate = FinanceService.RATES_DISPLAY.get("USD", {}).get("val", 0.0)
        
        self.txt_cotacao_display.value = f"Dólar Hoje: R$ {rate:.2f}"
        self.txt_cotacao_display.color = ft.Colors.GREEN if rate > 0 else ft.Colors.RED
        self.txt_cotacao_display.update()

    # --- FORMATADORES INTELIGENTES (ATM Style) ---
    
    def _format_currency_live(self, e):
        """Transforma '1500' em '15,00' -> '1.500,00'"""
        raw_val = "".join(filter(str.isdigit, e.control.value))
        if not raw_val:
            e.control.value = ""
            e.control.update()
            return
            
        val_float = int(raw_val) / 100
        # Formata no padrão brasileiro
        formatted = "{:,.2f}".format(val_float).replace(",", "X").replace(".", ",").replace("X", ".")
        e.control.value = formatted
        e.control.update()

    def _on_value_change(self, e):
        self._format_currency_live(e)
        self.results_area.controls.clear() # Limpa resultado se mudar valor
        self.results_area.update()

    def _parse_brl_input(self, text):
        """Converte '1.500,00' para float 1500.00"""
        if not text: return 0.0
        clean = text.replace(".", "").replace(",", ".")
        try: return float(clean)
        except: return 0.0

    # ---------------------------------------------

    def _mudanca_tipo_cambio(self, e):
        is_manual = (self.rg_cambio.value == "manual")
        self.tf_cotacao_manual.disabled = not is_manual
        self.tf_cotacao_manual.value = "" if not is_manual else self.tf_cotacao_manual.value
        
        if is_manual:
            self.txt_cotacao_display.value = "Usando valor manual"
            self.txt_cotacao_display.color = ft.Colors.ORANGE
            self.tf_cotacao_manual.focus()
        else:
            self.page_ref.run_task(self._fetch_rates_init)
            
        self.update()

    def _criar_switch_risco(self, label, cor):
        return ft.Switch(label=label, active_color=cor)

    def _calcular_click(self, e):
        # 1. Parse do Valor (USD)
        val_usd = self._parse_brl_input(self.tf_valor.value)
        
        if val_usd <= 0:
            self.tf_valor.error_text = "Digite um valor"
            self.update()
            return
        
        # 2. Parse da Cotação (se manual)
        manual_rate = None
        if self.rg_cambio.value == "manual":
            manual_rate = self._parse_brl_input(self.tf_cotacao_manual.value)
            if manual_rate <= 0:
                self.tf_cotacao_manual.error_text = "Digite a cotação"
                self.update()
                return

        self.tf_valor.error_text = None
        self.tf_cotacao_manual.error_text = None
        self.results_area.controls = []

        # 3. Verifica Crime
        crime_alert = TaxEngine.check_criminal_risk(
            ocultacao=self.sw_ocultacao.value,
            quantidade_excessiva=self.sw_quantidade.value,
            reincidente=self.sw_reincidente.value
        )

        if crime_alert:
            self._mostrar_alerta_crime(crime_alert)
        else:
            self._mostrar_cenarios_financeiros(val_usd, manual_rate)

        self.update()

    def _mostrar_alerta_crime(self, alert_data):
        card = ft.Container(
            gradient=ft.LinearGradient(
                colors=[ft.Colors.RED_900, ft.Colors.BLACK],
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1)
            ),
            padding=20,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.RED_500),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.GAVEL, color=ft.Colors.WHITE, size=30),
                    ft.Text("RISCO PENAL", weight="bold", size=18, color=ft.Colors.WHITE)
                ]),
                ft.Divider(color=ft.Colors.WHITE24),
                ft.Text(alert_data["msg"], size=15, weight="bold", color=ft.Colors.RED_100),
                ft.Text(alert_data["detalhe"], size=13, color=ft.Colors.WHITE70),
            ])
        )
        self.results_area.controls.append(card)

    def _mostrar_cenarios_financeiros(self, val_usd, manual_rate):
        report = TaxEngine.calculate_scenarios(val_usd, manual_rate=manual_rate)
        
        # Info de resumo
        dolar = report["meta"]["dolar_usado"]
        cota = report["meta"]["cota_usd"]
        
        self.results_area.controls.append(
            ft.Container(
                bgcolor=ft.Colors.BLUE_GREY_900,
                padding=10, border_radius=8,
                content=ft.Row([
                    ft.Icon(ft.Icons.INFO, size=16, color=ft.Colors.CYAN),
                    ft.Text(f"Cálculo base: US$ {cota:.0f} de isenção | Dólar R$ {dolar:.2f}", size=12)
                ], alignment=ft.MainAxisAlignment.CENTER)
            )
        )
        
        for cenario in report["scenarios"]:
            self.results_area.controls.append(self._build_scenario_card(cenario))

    def _build_scenario_card(self, data):
        cor_tema = ft.Colors.GREY
        icone = ft.Icons.CIRCLE
        if data["cor"] == "green": 
            cor_tema = ft.Colors.GREEN
            icone = ft.Icons.CHECK_CIRCLE
        elif data["cor"] == "orange": 
            cor_tema = ft.Colors.ORANGE
            icone = ft.Icons.WARNING_AMBER
        elif data["cor"] == "red": 
            cor_tema = ft.Colors.RED
            icone = ft.Icons.BLOCK
        elif data["cor"] == "blue": 
            cor_tema = ft.Colors.BLUE
            icone = ft.Icons.STOREFRONT

        def fmt(x):
            return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return ft.Container(
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            border_radius=10,
            border=ft.border.only(left=ft.BorderSide(6, cor_tema)),
            padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Icon(icone, color=cor_tema),
                    ft.Text(data["titulo"], weight="bold", size=15, expand=True),
                ]),
                ft.Container(height=5),
                ft.Row([
                    ft.Text("Custo Total:", color=ft.Colors.GREY_400, size=14),
                    ft.Text(fmt(data['total_geral']), weight="bold", size=16, color=ft.Colors.WHITE)
                ], alignment="spaceBetween"),
                ft.Divider(color=ft.Colors.WHITE10, height=10),
                self._row_detalhe("Imposto:", fmt(data["imposto"])),
                self._row_detalhe("Multa:", fmt(data["multa"]), 
                                  color=ft.Colors.RED_300 if data["multa"] > 0 else ft.Colors.GREY_500),
                ft.Container(height=5),
                ft.Text(data['risco'], size=12, color=ft.Colors.CYAN_100, italic=True)
            ])
        )

    def _row_detalhe(self, label, valor, color=ft.Colors.WHITE):
        return ft.Row([
            ft.Text(label, color=ft.Colors.GREY_400, size=13),
            ft.Text(valor, color=color, weight="bold", size=13)
        ], alignment="spaceBetween")