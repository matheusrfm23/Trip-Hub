import flet as ft
import random
import time
import json
import os
import threading
from src.core.config import ASSETS_DIR
from src.core.locker import file_lock

try:
    from word_search_generator import WordSearch
except ImportError:
    WordSearch = None 

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
SCORE_FILE = os.path.join(ASSETS_DIR, "data", "word_search_scores.json")
COST_HINT = 100
SCORE_BASE = 20
SCORE_BONUS_MAX = 10

FULL_WORD_DB = {
    "✈️ Aeroporto": [
        "PASSAPORTE", "VISTO", "EMBARQUE", "ADUANA", "MALAS", "RAIOX", "GUICHE", "CONEXAO", 
        "CHECKIN", "PORTAO", "IMIGRACAO", "ESCALA", "ATRASO", "DECOLAR", "PISTA", "TORRE", 
        "PILOTO", "COMISSARIA", "PASSAGEM", "BILHETE", "ESTEIRA", "CARRINHO", "TAXFREE", 
        "DOLAR", "CAMBIO", "TERMINAL", "FINGER", "LOJAS", "POLICIA", "ALFANDEGA", "VACINA"
    ],
    "💺 No Avião": [
        "TURBULENCIA", "PILOTO", "JANELA", "CORREDOR", "CINTO", "POUSO", "DECOLAGEM", "ASAS", 
        "TURBINA", "FONES", "FILME", "COBERTOR", "REFEICAO", "AGUA", "CAFE", "CAPITAO", 
        "BANHEIRO", "EMERGENCIA", "MASCARA", "OXIGENIO", "REVISTA", "MAPA", "NUVENS", "CEU", 
        "POLTRONA", "MESA", "EXECUTIVA", "ECONOMICA"
    ],
    "🏖️ Férias": [
        "PRAIA", "HOTEL", "PISCINA", "RELAXAR", "PASSEIO", "FOTOS", "SOL", "MAR", "AREIA", 
        "SORVETE", "TURISTA", "MAPA", "GUIA", "MUSEU", "PARQUE", "TRILHA", "CACHOEIRA", 
        "MONTANHA", "MERGULHO", "BARCO", "NAVIO", "CRUZEIRO", "RESORT", "POUSADA", "HOSTEL", 
        "CAMPING", "FOGUEIRA", "VIOLAO", "AMIGOS", "FAMILIA", "LEMBRANCAS"
    ],
    "🎒 Bagagem": [
        "ROUPAS", "NECESSAIRE", "CARREGADOR", "ADAPTADOR", "OCULOS", "TENIS", "CHINELO", 
        "CASACO", "REMEDIOS", "LIVRO", "DOCUMENTOS", "ESCOVA", "PASTA", "SHAMPOO", "SABONETE", 
        "PERFUME", "DESODORANTE", "PROTETOR", "MAQUIAGEM", "PIJAMA", "MEIAS", "TOALHA", "CHAPEU", 
        "BONE", "LUVA", "JAQUETA", "BERMUDA", "CAMISETA", "VESTIDO", "BOLSA", "MOCHILA", "CADEADO"
    ],
    "🌍 Países": [
        "BRASIL", "ARGENTINA", "CHILE", "URUGUAI", "PERU", "COLOMBIA", "EUA", "CANADA", 
        "MEXICO", "ESPANHA", "PORTUGAL", "FRANCA", "ITALIA", "ALEMANHA", "INGLATERRA", 
        "JAPAO", "CHINA", "INDIA", "AUSTRALIA", "EGITO", "GRECIA", "TURQUIA", "RUSSIA"
    ]
}

class WordSearchGame(ft.Container):
    def __init__(self, page: ft.Page, on_exit):
        super().__init__()
        self.main_page = page
        self.on_exit = on_exit
        self.expand = True
        self.padding = 0 
        
        self.high_score = self._load_high_score()
        self.score = 0
        self.level = 1
        
        self.puzzle = []      
        self.words_to_find = set() 
        self.found_words = set()   
        self.grid_size = 10   
        self.selected_start = None 
        self.current_theme = ""
        self.grid_controls = []
        
        self.start_time = 0
        self.last_found_time = 0 
        self.timer_running = False
        self.timer_thread = None 
        
        if WordSearch is None:
            self.content = self._build_error_screen()
        else:
            self.content = self._build_theme_selector()

    def _load_high_score(self):
        if not os.path.exists(SCORE_FILE): return 0
        try:
            with open(SCORE_FILE, "r") as f:
                return json.load(f).get("high_score", 0)
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

    def _stop_timer(self):
        self.timer_running = False

    def _exit_game(self):
        self._stop_timer()
        self.on_exit()

    def _build_error_screen(self):
        return ft.Column([
            ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=50),
            ft.Text("Biblioteca ausente!", size=20, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton("Voltar", on_click=lambda e: self._exit_game())
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _build_theme_selector(self):
        buttons = []
        buttons.append(
            ft.ElevatedButton(
                content=ft.Row([ft.Icon(ft.Icons.SHUFFLE), ft.Text("MODO ALEATÓRIO")], alignment=ft.MainAxisAlignment.CENTER),
                width=220, height=50,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), bgcolor=ft.Colors.PURPLE_900, color=ft.Colors.WHITE),
                on_click=lambda e: self._start_game("Aleatório", reset_score=True)
            )
        )
        for theme in FULL_WORD_DB.keys():
            buttons.append(
                ft.ElevatedButton(
                    content=ft.Text(theme), width=220, height=50,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE),
                    on_click=lambda e, t=theme: self._start_game(t, reset_score=True)
                )
            )

        return ft.Column([
            ft.Container(height=20),
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self._exit_game(), icon_color=ft.Colors.GREY_300),
                ft.Column([
                    ft.Text("Caça Palavras", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Recorde: {self.high_score}", size=12, color=ft.Colors.AMBER)
                ], spacing=0)
            ]),
            ft.Divider(color=ft.Colors.GREY_800),
            ft.Container(
                content=ft.Column(buttons, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, scroll=ft.ScrollMode.AUTO),
                alignment=ft.Alignment(0, 0), expand=True
            )
        ])

    def _start_game(self, theme, reset_score=False, next_level=False):
        if reset_score:
            self.score = 0
            self.level = 1
            self.grid_size = 10
        elif next_level:
            self.level += 1
            self.grid_size = min(10 + (self.level // 2), 14) 
        
        self.current_theme = theme
        self.start_time = time.time()
        self.last_found_time = time.time()
        num_words = min(8 + self.level, 15)
        
        if theme == "Aleatório":
            all_words = [w for sublist in FULL_WORD_DB.values() for w in sublist]
            selected_words = random.sample(all_words, num_words)
        else:
            theme_words = FULL_WORD_DB[theme]
            count = min(len(theme_words), num_words)
            selected_words = random.sample(theme_words, count)

        ws = WordSearch(",".join(selected_words), level=2, size=self.grid_size)
        self.puzzle = ws.puzzle
        self.words_to_find = {word.text for word in ws.words}
        self.found_words = set()
        self.selected_start = None
        self.grid_controls = [] 
        self.word_list_container = ft.Container(padding=10, bgcolor=ft.Colors.BLUE_GREY_900, border_radius=10)
        self.timer_text = ft.Text("00:00", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        
        self._build_game_ui()
        self._stop_timer()
        self.timer_running = True
        self.timer_thread = threading.Thread(target=self._update_timer, daemon=True)
        self.timer_thread.start()

    def _update_timer(self):
        while self.timer_running:
            try:
                elapsed = int(time.time() - self.start_time)
                mins, secs = divmod(elapsed, 60)
                self.timer_text.value = f"{mins:02}:{secs:02}"
                self.timer_text.update()
                time.sleep(1)
            except: break

    def _calculate_cell_size(self):
        screen_width = self.main_page.window_width if self.main_page.window_width > 0 else 360
        if screen_width > 1200: screen_width = 400
        available_width = screen_width - 20 # Margem lateral
        cell_size = (available_width - (self.grid_size * 2)) / self.grid_size # Desconta espaçamentos
        return max(20, cell_size)

    def _build_game_ui(self):
        cell_size = self._calculate_cell_size()
        font_size = cell_size * 0.55

        # Barra Superior
        top_bar = ft.Container(
            content=ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self._reset_to_menu(), icon_size=20),
                ft.Column([
                    ft.Row([ft.Icon(ft.Icons.TIMER, size=14), self.timer_text], spacing=5),
                    ft.Text(f"Nível {self.level}", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER, size=12)
                ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB, color=ft.Colors.YELLOW, size=16),
                        ft.Text(f"Dica (-{COST_HINT})", size=11, weight=ft.FontWeight.BOLD)
                    ], spacing=2),
                    padding=5, border=ft.border.all(1, ft.Colors.YELLOW), border_radius=5,
                    on_click=lambda e: self._use_hint(), ink=True
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=10, vertical=5), bgcolor=ft.Colors.GREY_900
        )

        # Construção da Grade Centralizada
        grid_rows = []
        for r in range(self.grid_size):
            row_controls = []
            for c in range(self.grid_size):
                letter = self.puzzle[r][c]
                btn = ft.Container(
                    content=ft.Text(letter, weight=ft.FontWeight.BOLD, size=font_size),
                    width=cell_size, height=cell_size, alignment=ft.Alignment(0, 0),
                    bgcolor=ft.Colors.GREY_900, border_radius=3,
                    on_click=lambda e, r=r, c=c: self._handle_tap(r, c),
                    data={"r": r, "c": c, "letter": letter, "status": "default"},
                    animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
                )
                row_controls.append(btn)
            grid_rows.append(ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=2))
            self.grid_controls.append(row_controls)

        self._update_word_list()

        # Layout Principal
        self.content = ft.Column([
            top_bar,
            ft.Container(
                content=ft.Column([
                    ft.Container(height=10),
                    # AREA DA GRADE - CENTRALIZADA SEM MARGENS LATERAIS QUE EMPURRAM
                    ft.Container(
                        content=ft.Column(grid_rows, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=0, alignment=ft.Alignment(0, 0)
                    ),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    ft.Row([
                        ft.Icon(ft.Icons.STAR, color=ft.Colors.GREEN, size=16),
                        ft.Text(f"Pontos: {self.score}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=10),
                    ft.Text("Palavras a encontrar:", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300, text_align=ft.TextAlign.CENTER),
                    self.word_list_container,
                    ft.Container(height=40) 
                ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER), 
                expand=True
            )
        ], spacing=0)
        self.update()

    def _update_word_list(self):
        chips = []
        for word in sorted(self.words_to_find):
            found = word in self.found_words
            bg_color = ft.Colors.GREEN_900 if found else ft.Colors.BLACK45
            text_color = ft.Colors.GREEN_200 if found else ft.Colors.WHITE
            chips.append(
                ft.Container(
                    content=ft.Text(word, size=10, color=text_color, opacity=0.4 if found else 1.0),
                    padding=5, bgcolor=bg_color, border_radius=6
                )
            )
        
        safe_width = self.main_page.window_width - 20 if self.main_page.window_width > 0 else 340
        self.word_list_container.content = ft.Row(controls=chips, wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=4, run_spacing=4, width=safe_width)
        try:
            if self.word_list_container.page: self.word_list_container.update()
        except: pass

    def _find_word_start(self, target_word):
        rows = self.grid_size
        cols = self.grid_size
        word_len = len(target_word)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        for r in range(rows):
            for c in range(cols):
                if self.puzzle[r][c] != target_word[0]: continue
                for dr, dc in directions:
                    if 0 <= r + (word_len - 1) * dr < rows and 0 <= c + (word_len - 1) * dc < cols:
                        match = True
                        for i in range(word_len):
                            if self.puzzle[r + i * dr][c + i * dc] != target_word[i]:
                                match = False
                                break
                        if match: return r, c
        return -1, -1

    def _use_hint(self):
        if self.score < COST_HINT:
            self._show_msg(f"Precisa de {COST_HINT} pts!", "red")
            return
        missing = list(self.words_to_find - self.found_words)
        if not missing: return
        target_word = random.choice(missing)
        r, c = self._find_word_start(target_word)
        if r != -1 and c != -1:
            self.score -= COST_HINT
            self._update_score_display()
            def flash_thread():
                try:
                    cell = self.grid_controls[r][c]
                    orig = cell.bgcolor 
                    for _ in range(4):
                        cell.bgcolor = ft.Colors.PURPLE
                        cell.update()
                        time.sleep(0.2)
                        cell.bgcolor = orig
                        cell.update()
                        time.sleep(0.2)
                except: pass
            threading.Thread(target=flash_thread, daemon=True).start()
        else: self._show_msg("Palavra não localizada", "red")

    def _update_score_display(self):
        self.score_text.value = f"{self.score}"
        self.update()

    def _handle_tap(self, r, c):
        if self.selected_start is None:
            self.selected_start = (r, c)
            self._highlight_cell(r, c, ft.Colors.AMBER_600)
            return
        start_r, start_c = self.selected_start
        if (start_r, start_c) == (r, c):
            self._reset_selection()
            return
        if self._check_selection(start_r, start_c, r, c):
            self.selected_start = None
            if len(self.found_words) == len(self.words_to_find): self._show_win_screen()
        else: self._reset_selection()

    def _reset_selection(self):
        if self.selected_start:
            r, c = self.selected_start
            is_found = self.grid_controls[r][c].data["status"] == "found"
            self._highlight_cell(r, c, ft.Colors.GREEN_700 if is_found else ft.Colors.GREY_900)
        self.selected_start = None

    def _highlight_cell(self, r, c, color):
        cell = self.grid_controls[r][c]
        cell.bgcolor = color
        cell.update()

    def _check_selection(self, r1, c1, r2, c2):
        dr, dc = r2 - r1, c2 - c1
        steps = max(abs(dr), abs(dc))
        if steps == 0 or (abs(dr) != abs(dc) and dr != 0 and dc != 0): return False
        sr, sc = dr // steps, dc // steps
        word_chars, coords = [], []
        for i in range(steps + 1):
            cr, cc = r1 + i * sr, c1 + i * sc
            word_chars.append(self.puzzle[cr][cc])
            coords.append((cr, cc))
        word_str = "".join(word_chars)
        found = None
        if word_str in self.words_to_find and word_str not in self.found_words: found = word_str
        elif word_str[::-1] in self.words_to_find and word_str[::-1] not in self.found_words: found = word_str[::-1]
        if found:
            self.found_words.add(found)
            bonus = max(0, int((30 - (time.time() - self.last_found_time)) * (SCORE_BONUS_MAX / 30)))
            self.score += SCORE_BASE + bonus
            self.last_found_time = time.time()
            self._update_score_display()
            self._update_word_list()
            for pr, pc in coords:
                self.grid_controls[pr][pc].data["status"] = "found"
                self._highlight_cell(pr, pc, ft.Colors.GREEN_700)
            return True
        return False

    def _show_msg(self, text, color):
        self.main_page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color, duration=1000)
        self.main_page.snack_bar.open = True
        self.main_page.update()

    def _show_win_screen(self):
        self._stop_timer()
        self._save_high_score()
        self.content = ft.Column([
            ft.Container(height=50),
            ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.YELLOW, size=80),
            ft.Text("NÍVEL CONCLUÍDO!", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.YELLOW),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Pontuação Total: {self.score}", weight=ft.FontWeight.BOLD, size=22, color=ft.Colors.GREEN),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), border_radius=10
            ),
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton("Menu", icon=ft.Icons.MENU, on_click=lambda e: self._reset_to_menu()),
                ft.FilledButton("Próximo Nível", icon=ft.Icons.ARROW_FORWARD, on_click=lambda e: self._start_game(self.current_theme, next_level=True), style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700))
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.update()

    def _reset_to_menu(self):
        self._stop_timer()
        self.high_score = self._load_high_score()
        self.content = self._build_theme_selector()
        self.update()