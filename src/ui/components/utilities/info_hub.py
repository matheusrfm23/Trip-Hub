# ARQUIVO: src/ui/components/utilities/info_hub.py
import flet as ft
from src.logic.protocol_service import ProtocolService

class InfoHub(ft.Container):
    def __init__(self, page: ft.Page, on_unlock_callback):
        super().__init__()
        self.page_ref = page
        self.on_unlock = on_unlock_callback 
        self.user_id = self.page_ref.user_profile["id"]
        
        # Estado de Leitura
        self.is_read = False 
        
        # Estado Interno das Abas
        self.current_tab_index = 0
        
        # Containers para atualização granular
        self.tabs_container = ft.Container() 
        self.content_container = ft.Container() 
        
        # --- ESTILOS ---
        self.border_radius = 15
        self.bgcolor = ft.Colors.BLACK
        self.padding = 0
        self.animate_opacity = 300
        
        # Inicializa vazio
        self.content = ft.Container(height=50)

    def did_mount(self):
        self.page_ref.run_task(self._load_state)

    async def _load_state(self):
        try:
            self.is_read = await ProtocolService.has_read(self.user_id)
        except:
            self.is_read = False
        self._render_main_layout()

    async def _save_state(self):
        try:
            await ProtocolService.mark_as_read(self.user_id)
        except: pass

    def _render_main_layout(self):
        self.border = ft.border.all(1, ft.Colors.RED_900 if not self.is_read else ft.Colors.GREEN_900)
        
        if self.is_read:
            self.content = self._build_collapsed_mode()
            if self.on_unlock: self.on_unlock() 
        else:
            self.content = self._build_reading_mode()
        
        self.update()

    # --- LÓGICA DE ABAS ---
    
    def _change_tab(self, index):
        self.current_tab_index = index
        self.tabs_container.content = self._build_manual_tabs_row()
        self.tabs_container.update()
        self.content_container.content = self._get_current_tab_content()
        self.content_container.update()

    def _build_manual_tabs_row(self):
        return ft.Row([
            self._build_tab_button(0, "PREPARAÇÃO", ft.Icons.BACKPACK),
            self._build_tab_button(1, "AEROPORTO", ft.Icons.AIRPLANE_TICKET),
            self._build_tab_button(2, "FRONTEIRAS", ft.Icons.LOCAL_POLICE),
            self._build_tab_button(3, "RETORNO", ft.Icons.ASSIGNMENT_RETURN),
        ], spacing=5)

    def _build_tab_button(self, index, text, icon):
        is_selected = (self.current_tab_index == index)
        color = ft.Colors.CYAN if is_selected else ft.Colors.GREY
        bg_color = ft.Colors.with_opacity(0.1, ft.Colors.CYAN) if is_selected else ft.Colors.TRANSPARENT
        
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=20),
                ft.Text(text, size=9, color=color, weight="bold")
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
            padding=10,
            bgcolor=bg_color,
            border_radius=8,
            on_click=lambda e: self._change_tab(index),
            expand=True,
            animate=200,
        )

    # --- [CORREÇÃO CRÍTICA] MÃO NO FOGO PELOS LINKS ---
    
    # 1. Manipulador Assíncrono Centralizado
    async def _handle_link_click(self, e):
        """Pega a URL do evento e chama o launch_url com await"""
        # Para botões, a URL está em e.control.data
        # Para Markdown, a URL vem direto em e.data (string)
        url = e.data if isinstance(e.data, str) and "http" in e.data else getattr(e.control, "data", None)
        
        if url:
            await self.page_ref.launch_url(url)

    # 2. Botão configurado com data=url
    def _action_btn(self, text, icon, url, color=ft.Colors.CYAN):
        return ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(icon, size=16, color=color),
                ft.Text(text, size=11, weight="bold", color=color)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.with_opacity(0.1, color),
                padding=10,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            data=url, # Guarda a URL aqui
            on_click=self._handle_link_click # Chama a função async
        )

    # 3. Markdown configurado com on_tap_link
    def _safe_markdown(self, text):
        return ft.Markdown(
            text,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=self._handle_link_click, # Chama a função async ao clicar no link do texto
            selectable=True
        )

    # --- CONTEÚDO RICO ---

    def _get_current_tab_content(self):
        if self.current_tab_index == 0: return self._tab_preparacao()
        if self.current_tab_index == 1: return self._tab_aeroporto()
        if self.current_tab_index == 2: return self._tab_fronteiras()
        if self.current_tab_index == 3: return self._tab_retorno()
        return ft.Container()

    def _tab_preparacao(self):
        return ft.Column([
            self._safe_markdown("""
### 🎒 1. DOCUMENTOS PESSOAIS (Porte Obrigatório)
Estes documentos devem estar na sua mão/mochila. **NUNCA DESPACHE.**

* **🆔 RG (Cédula de Identidade):**
    * **DATA:** Deve ser posterior a **Março/2016** (menos de 10 anos).
    * **ESTADO:** Sem rasgos, sem plástico aberto.
    * **OBS:** RG Digital **NÃO É ACEITO**.
* **🛂 PASSAPORTE:** Válido. É o documento "imparável".
* **⛔ CNH:** **NÃO ENTRA** na Argentina/Paraguai. Só serve para dirigir.

### 💉 2. SAÚDE & VACINAS (Crítico)
* **FEBRE AMARELA (CIVP):**
    * **Exigência:** OBRIGATÓRIA para brasileiros.
    * **Fiscalização:** Rigorosa na entrada do Paraguai.
* **🇦🇷 SEGURO VIAGEM (ARGENTINA):**
    * **Regra:** Apólice impressa deve conter a frase: **"Despesas por COVID-19"**.
            """),
            ft.Divider(),
            ft.Text("LINKS OBRIGATÓRIOS:", weight="bold", size=12, color=ft.Colors.WHITE),
            ft.Row([
                self._action_btn("Emitir CIVP", ft.Icons.VACCINES, "https://www.gov.br/pt-br/servicos/obter-o-certificado-internacional-de-vacinacao-e-profilaxia", ft.Colors.YELLOW),
                self._action_btn("ConecteSUS", ft.Icons.MEDICAL_SERVICES, "https://conectesus-paciente.saude.gov.br/", ft.Colors.BLUE),
                self._action_btn("Antecedentes PF", ft.Icons.SECURITY, "https://www.gov.br/pf/pt-br/assuntos/antecedentes-criminais")
            ], wrap=True)
        ], scroll=ft.ScrollMode.ALWAYS)

    def _tab_aeroporto(self):
        return ft.Column([
            self._safe_markdown("""
### ✈️ AEROPORTO (BH -> FOZ)
**👜 BAGAGEM DE MÃO (Com você):**
* **🔋 Power Bank / Baterias:** **OBRIGATÓRIO** ir na mão.
* **💧 Líquidos:** Voo doméstico = máx 500ml.

**🧳 BAGAGEM DESPACHADA:**
* **NÃO COLOQUE:** Joias, dinheiro, câmeras ou notebook.
            """),
            ft.Divider(),
            self._action_btn("Regras Bagagem (ANAC)", ft.Icons.AIRPLANE_TICKET, "https://www.gov.br/anac/pt-br/assuntos/passageiros/bagagem")
        ], scroll=ft.ScrollMode.ALWAYS)

    def _tab_fronteiras(self):
        return ft.Column([
            self._safe_markdown("""
### 🚧 CRUZANDO AS PONTES

**🇦🇷 BRASIL -> ARGENTINA (Puerto Iguazú):**
* **Imigração:** Todos descem do carro com **RG (<10 anos)**.
* **Taxa Ecoturística:** Tenha dinheiro trocado (~R$ 20).

**🇵🇾 BRASIL -> PARAGUAI (Ciudad del Este):**
* **Compras:** Limite de isenção de **US$ 500,00**.
* **🚨 SEGURANÇA:** Vá direto às lojas grandes (Cellshop, Nissei, Monalisa). **IGNORE** guias de rua.
            """),
        ], scroll=ft.ScrollMode.ALWAYS)

    def _tab_retorno(self):
        return ft.Column([
            self._safe_markdown("""
### 🔙 O RETORNO (Aeroporto Foz -> BH)
**📦 COTA: US$ 500,00 (Via Terrestre)**
* Mesmo voltando de avião, sua cota é $500.

**👮‍♂️ O RAIO-X DA RECEITA:**
* Antes do check-in, **TODAS** as malas passam no scanner.
* Passou de $500? Declare no app e-DBV e pague na ponte.
            """),
            ft.Divider(),
            self._action_btn("Preencher e-DBV", ft.Icons.MONETIZATION_ON, "https://www.edbv.receita.fazenda.gov.br/", ft.Colors.GREEN)
        ], scroll=ft.ScrollMode.ALWAYS)

    # --- INTERFACE INTERNA ---
    def _build_internal_interface(self):
        self.tabs_container.content = self._build_manual_tabs_row()
        self.content_container.content = self._get_current_tab_content()
        self.content_container.height = 400 
        self.content_container.border = ft.border.all(1, ft.Colors.WHITE10)
        self.content_container.border_radius = 10
        self.content_container.padding = 5
        self.content_container.bgcolor = ft.Colors.with_opacity(0.02, ft.Colors.WHITE)

        return ft.Column([
            self.tabs_container,
            ft.Container(height=10),
            self.content_container
        ])

    # --- MODO 1: LEITURA OBRIGATÓRIA ---
    def _build_reading_mode(self):
        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.GPP_MAYBE, color=ft.Colors.RED, size=30),
                    ft.Column([
                        ft.Text("PROTOCOLO DE SEGURANÇA", size=18, weight="bold", color=ft.Colors.RED),
                        ft.Text("Leia atentamente todas as abas.", size=12, color=ft.Colors.WHITE70)
                    ], spacing=0, expand=True)
                ]),
                ft.Divider(color=ft.Colors.RED_900),
                
                self._build_internal_interface(),
                
                ft.Container(height=15),
                
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE),
                        ft.Text("LI, ENTENDI E CONCORDO", weight="bold")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN_700,
                        color=ft.Colors.WHITE,
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    width=float('inf'),
                    on_click=lambda e: self.page_ref.run_task(self._mark_as_read_click, e)
                )
            ])
        )

    # --- MODO 2: RECOLHIDO ---
    def _build_collapsed_mode(self):
        return ft.ExpansionTile(
            title=ft.Text("Protocolos Oficiais (Conferido)", size=16, weight="bold", color=ft.Colors.GREEN_400),
            subtitle=ft.Text("Clique para consultar documentos", size=12, color=ft.Colors.GREY),
            leading=ft.Icon(ft.Icons.VERIFIED_USER, color=ft.Colors.GREEN),
            bgcolor=ft.Colors.TRANSPARENT,
            maintain_state=True,
            controls=[
                ft.Container(
                    padding=20,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    content=ft.Column([
                        ft.Text("LINKS RÁPIDOS:", weight="bold", color=ft.Colors.CYAN),
                        ft.Row([
                            self._action_btn("CIVP", ft.Icons.VACCINES, "https://www.gov.br/pt-br/servicos/obter-o-certificado-internacional-de-vacinacao-e-profilaxia"),
                            self._action_btn("e-DBV", ft.Icons.ATTACH_MONEY, "https://www.edbv.receita.fazenda.gov.br/"),
                            self._action_btn("Antecedentes", ft.Icons.SECURITY, "https://www.gov.br/pf/pt-br/assuntos/antecedentes-criminais")
                        ], wrap=True),
                        ft.Divider(),
                        ft.Text("GUIA COMPLETO:", weight="bold", color=ft.Colors.WHITE70),
                        self._build_internal_interface() 
                    ])
                )
            ]
        )

    async def _mark_as_read_click(self, e):
        self.is_read = True
        await self._save_state()
        self._render_main_layout()
        
        if self.on_unlock:
            self.on_unlock()
            
        try:
            snack = ft.SnackBar(content=ft.Text("Protocolos salvos. Boa viagem!"), bgcolor=ft.Colors.GREEN_700)
            self.page_ref.overlay.append(snack) 
            snack.open = True
            self.page_ref.update()
        except: pass