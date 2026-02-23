import flet as ft
import random
import json
import os
from src.core.config import ASSETS_DIR
from src.core.locker import file_lock

# Arte ASCII para os estágios da forca
HANGMAN_STAGES = [
    """
      +---+
      |   |
          |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
      |   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     /    |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     / \\  |
          |
    =========
    """
]

WORDS_DB = {
    "✈️ Aeroporto": [
        "TERMINAL", "PASSAPORTE", "ALFANDEGA", "BAGAGEM", "CONEXAO", 
        "CHECKIN", "EMBARQUE", "RAIOX", "IMIGRACAO", "VISA",
        "ESTEIRA", "PORTAO", "ATRASO", "ESCALA", "VIP",
        "FREESHOP", "MOCHILA", "DETECTOR", "METAL", "POLICIA",
        "CONTROLADOR", "PISTA", "HANGAR", "CARRINHO", "GUICHE",
        "PASSAGEM", "BILHETE", "OVERBOOKING", "BALCAO", "PAINEL",
        "FUSOHORARIO", "CAMBIO", "DOLAR", "EURO", "TAXI"
    ],
    "💺 No Avião": [
        "TURBULENCIA", "DECOLAGEM", "POUSO", "PILOTO", "COMISSARIA", 
        "JANELA", "CORREDOR", "FONES", "FILMES", "NUVENS",
        "ASSENTO", "CINTO", "MESA", "LAVATORIO", "TURBINA",
        "ASA", "CAUDA", "TREMDEPOUSO", "MASCARA", "OXIGENIO",
        "COLETE", "SALVAVIDAS", "JANTAR", "LANCHE", "AGUA",
        "TRAVESSEIRO", "MANTA", "REVISTA", "EMERGENCIA", "SAIDA",
        "PRIMEIRACLASSE", "EXECUTIVA", "ECONOMICA", "CABINE", "CAPITAO"
    ],
    "🏖️ Destino": [
        "HOTEL", "PASSEIO", "RESTAURANTE", "MUSEU", "PRAIA", 
        "PISCINA", "TRILHA", "MONUMENTO", "SUITE", "VISTA",
        "MONTANHA", "FLORESTA", "CIDADE", "PONTE", "PARQUE",
        "CASTELO", "IGREJA", "TEATRO", "ESTADIO", "SHOPPING",
        "MERCADO", "FEIRA", "BARCO", "ILHA", "CACHOEIRA",
        "DESERTO", "NEVE", "ESQUI", "MERGULHO", "SAFARI",
        "RESORT", "POUSADA", "HOSTEL", "ACAMPAMENTO", "CRUZEIRO"
    ],
    "🎒 Itens": [
        "CAMERA", "PROTETOR", "OCULOS", "MAPA", "CARREGADOR", 
        "ADAPTADOR", "DINHEIRO", "ROUPAS", "NECESSAIRE", "DOCUMENTOS",
        "REMEDIOS", "LIVRO", "TABLET", "BONÉ", "CHAPEU",
        "CHINELO", "TENIS", "BOTA", "CASACO", "JAQUETA",
        "CACHECOL", "LUVA", "MEIA", "PIJAMA", "ESCOVA",
        "PASTA", "SABONETE", "SHAMPOO", "PERFUME", "MAQUIAGEM",
        "POWERBANK", "NOTEBOOK", "FONE", "ALMOFADA", "LANTERNA"
    ]
}

SCORE_FILE = os.path.join(ASSETS_DIR, "data", "hangman_scores.json")

class HangmanGame(ft.Container):
    def __init__(self, page: ft.Page, on_exit):
        super().__init__()
        self.main_page = page 
        self.on_exit = on_exit
        self.expand = True
        self.padding = 10
        
        # Estado Global
        self.score = 0
        self.streak = 0
        self.high_score = self._load_high_score()
        
        # Estado da Rodada
        self.current_theme = ""
        self.current_word = ""
        self.guessed_letters = set()
        self.errors = 0
        self.game_over = False
        
        # Inicia na seleção
        self.content = self._build_theme_selector()

    # --- PERSISTÊNCIA DE RECORDE ---
    def _load_high_score(self):
        if not os.path.exists(SCORE_FILE): return 0
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except: return 0

    def _save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
                with file_lock():
                    with open(SCORE_FILE, "w") as f:
                        json.dump({"high_score": self.high_score}, f)
            except: pass

    # --- TELA 1: SELEÇÃO DE TEMA ---
    def _build_theme_selector(self):
        buttons = []
        buttons.append(
            ft.ElevatedButton(
                content=ft.Row([ft.Icon(ft.Icons.SHUFFLE), ft.Text("MODO ALEATÓRIO")], alignment=ft.MainAxisAlignment.CENTER),
                width=220, height=50,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), bgcolor=ft.Colors.PURPLE_900, color=ft.Colors.WHITE),
                on_click=lambda e: self._init_new_game("Aleatório", reset_score=True)
            )
        )
        for theme in WORDS_DB.keys():
            buttons.append(
                ft.ElevatedButton(
                    content=ft.Text(theme),
                    width=220, height=50,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE),
                    on_click=lambda e, t=theme: self._init_new_game(t, reset_score=True)
                )
            )

        return ft.Column([
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_exit(), icon_color=ft.Colors.GREY_300),
                ft.Column([
                    ft.Text("Jogo da Forca", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Recorde: {self.high_score}", size=12, color=ft.Colors.AMBER)
                ], spacing=0)
            ]),
            ft.Divider(color=ft.Colors.GREY_800),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.VIDEOGAME_ASSET, size=60, color=ft.Colors.CYAN),
                        ft.Text("Viagem Segura", size=14, color=ft.Colors.GREY),
                        ft.Container(height=10),
                        *buttons
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO
                ),
                alignment=ft.Alignment(0, 0),
                expand=True
            )
        ])

    def _init_new_game(self, theme, reset_score=False):
        if reset_score:
            self.score = 0
            self.streak = 0
        
        self.current_theme = theme
        if theme == "Aleatório":
            all_words = [w for sublist in WORDS_DB.values() for w in sublist]
            self.current_word = random.choice(all_words)
        else:
            self.current_word = random.choice(WORDS_DB[theme])
            
        self.guessed_letters = set()
        self.errors = 0
        self.game_over = False
        
        self._build_game_screen()

    # --- TELA 2: O JOGO ---
    def _build_game_screen(self):
        # Componentes
        self.img_display = ft.Text(value=HANGMAN_STAGES[0], font_family="monospace", size=14, color=ft.Colors.YELLOW)
        self.word_display = ft.Row(alignment=ft.MainAxisAlignment.CENTER, wrap=True)
        self.keyboard_container = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Header Info
        self.score_text = ft.Text(f"Pontos: {self.score}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        
        # Botão Dica
        self.hint_btn = ft.IconButton(
            icon=ft.Icons.LIGHTBULB, 
            icon_color=ft.Colors.YELLOW, 
            tooltip="Dica (-20 pontos)",
            on_click=lambda e: self._use_hint()
        )
        
        # Botão Vida Extra (NOVO)
        self.life_btn = ft.IconButton(
            icon=ft.Icons.FAVORITE, 
            icon_color=ft.Colors.RED, 
            tooltip="Recuperar Vida (-50 pontos)",
            on_click=lambda e: self._buy_life()
        )

        # Container Principal do Jogo (será substituído ao fim do jogo)
        self.game_area = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.img_display,
                    bgcolor=ft.Colors.BLACK54,
                    padding=10,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.GREY_800)
                ),
                ft.Container(height=10),
                self.word_display,
                ft.Container(height=20),
                self.keyboard_container
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
            expand=True,
            alignment=ft.Alignment(0, -0.5) 
        )

        self.content = ft.Column([
            # Top Bar
            ft.Row([
                ft.IconButton(ft.Icons.CLOSE, on_click=lambda e: self._reset_to_menu(), tooltip="Desistir"),
                ft.Column([
                    self.score_text,
                    ft.Text(f"Tema: {self.current_theme}", size=10, color=ft.Colors.GREY)
                ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.life_btn, self.hint_btn], spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Área Dinâmica (Jogo ou Tela Final)
            self.game_area
        ])
        
        self._update_word_display()
        self._generate_keyboard()
        self.update()

    # --- LÓGICA DO JOGO ---
    def _buy_life(self):
        """Remove um membro do boneco por 50 pontos"""
        if self.game_over: return
        
        if self.errors <= 0:
            self._show_msg("Vida cheia!", "green")
            return
            
        if self.score < 50:
            self._show_msg("Precisa de 50 pontos!", "red")
            return
            
        # Aplica a compra
        self.score -= 50
        self.errors -= 1
        
        # Atualiza UI
        self.score_text.value = f"Pontos: {self.score}"
        self.score_text.update()
        
        self.img_display.value = HANGMAN_STAGES[self.errors]
        self.img_display.update()
        
        self._show_msg("Vida recuperada! (-50 pts)", "red")

    def _use_hint(self):
        if self.game_over: return
        if self.score < 20:
            self._show_msg("Precisa de 20 pontos!", "amber")
            return

        unknowns = [l for l in self.current_word if l not in self.guessed_letters]
        if not unknowns: return
        
        reveal = random.choice(unknowns)
        self.score -= 20
        self.score_text.value = f"Pontos: {self.score}"
        self.score_text.update()
        
        self._show_msg("Dica usada! (-20 pts)", "amber")
        self._guess(reveal)

    def _show_msg(self, text, color):
        self.main_page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color, duration=1000)
        self.main_page.snack_bar.open = True
        self.main_page.update()

    def _update_word_display(self, reveal_all=False):
        self.word_display.controls = []
        won = True
        
        for letter in self.current_word:
            is_revealed = letter in self.guessed_letters or reveal_all
            if not is_revealed: won = False
            
            color = ft.Colors.WHITE
            if reveal_all:
                color = ft.Colors.GREEN if letter in self.guessed_letters else ft.Colors.RED
            
            self.word_display.controls.append(
                ft.Container(
                    content=ft.Text(letter if is_revealed else "_", size=28, weight=ft.FontWeight.BOLD, color=color),
                    padding=5,
                    border=ft.border.only(bottom=ft.border.BorderSide(2, ft.Colors.WHITE24))
                )
            )
        
        # Checa vitória/derrota apenas se não estamos no modo de revelação final
        if not reveal_all:
            if won: self._handle_win()
            elif self.errors >= 6: self._handle_loss()
        
        try:
            if self.word_display.page: self.word_display.update()
        except: pass

    def _generate_keyboard(self):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        keys = []
        for char in alphabet:
            is_disabled = char in self.guessed_letters or self.game_over
            btn_color = ft.Colors.GREY_800
            
            if char in self.guessed_letters:
                btn_color = ft.Colors.GREEN_900 if char in self.current_word else ft.Colors.RED_900

            keys.append(
                ft.Container(
                    content=ft.Text(char, size=16, weight=ft.FontWeight.BOLD),
                    width=40, height=40,
                    bgcolor=btn_color,
                    border_radius=5,
                    alignment=ft.Alignment(0, 0),
                    on_click=None if is_disabled else lambda e, c=char: self._guess(c),
                    opacity=0.3 if is_disabled else 1.0,
                    animate_opacity=300
                )
            )
            
        self.keyboard_container.controls = [
            ft.Row(controls=keys, wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=5, run_spacing=5)
        ]
        
        try:
            if self.keyboard_container.page: self.keyboard_container.update()
        except: pass

    def _guess(self, letter):
        if self.game_over: return
        self.guessed_letters.add(letter)
        
        if letter not in self.current_word:
            self.errors += 1
            if self.errors < len(HANGMAN_STAGES):
                self.img_display.value = HANGMAN_STAGES[self.errors]
                try: self.img_display.update()
                except: pass
        
        self._update_word_display()
        self._generate_keyboard()

    def _handle_win(self):
        self.game_over = True
        self.streak += 1
        points = 10 + ((6 - self.errors) * 5) + (self.streak * 2)
        self.score += points
        self.score_text.value = f"Pontos: {self.score}"
        self._save_high_score()
        self._show_end_screen(True, points)

    def _handle_loss(self):
        self.game_over = True
        self.streak = 0
        self._save_high_score()
        self._update_word_display(reveal_all=True)
        self._show_end_screen(False, 0)

    def _show_end_screen(self, won, points):
        # Aqui substituímos o CONTEÚDO da área do jogo, garantindo que os botões apareçam
        msg_color = ft.Colors.GREEN if won else ft.Colors.RED
        msg_title = "VITÓRIA!" if won else "GAME OVER"
        
        if won:
            subtext = f"+{points} pontos\nSequência: {self.streak}x"
            btn_text = "Próxima Palavra"
            btn_icon = ft.Icons.ARROW_FORWARD
            btn_action = lambda e: self._init_new_game(self.current_theme, reset_score=False)
        else:
            subtext = f"A palavra era: {self.current_word}"
            btn_text = "Tentar Novamente"
            btn_icon = ft.Icons.REFRESH
            btn_action = lambda e: self._init_new_game(self.current_theme, reset_score=True)

        # Novo conteúdo para a área central
        end_content = ft.Column([
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.EMOJI_EVENTS if won else ft.Icons.SENTIMENT_VERY_DISSATISFIED, size=50, color=msg_color),
                    ft.Text(msg_title, size=24, weight=ft.FontWeight.BOLD, color=msg_color),
                    ft.Text(subtext, size=16, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.Colors.with_opacity(0.1, msg_color),
                border_radius=10,
                border=ft.border.all(1, ft.Colors.with_opacity(0.3, msg_color))
            ),
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton(content=ft.Text("Menu"), icon=ft.Icons.MENU, on_click=lambda e: self._reset_to_menu()),
                ft.FilledButton(content=ft.Text(btn_text), icon=btn_icon, on_click=btn_action)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # SUBSTITUIÇÃO CRÍTICA: Trocamos o conteúdo do container game_area
        self.game_area.content = end_content
        self.game_area.update()
        
        # Atualiza pontuação final no header
        self.score_text.update()

    def _reset_to_menu(self):
        self.high_score = self._load_high_score()
        self.content = self._build_theme_selector()
        self.update()