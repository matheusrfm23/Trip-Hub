import flet as ft
from src.ui.components.leisure.hangman import HangmanGame
from src.ui.components.leisure.word_search import WordSearchGame # <--- IMPORT NOVO

class GameHub(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.padding = 20
        
        self.menu_content = self._build_menu()
        self.content = self.menu_content

    def _build_menu(self):
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.GAMES_OUTLINED, size=30, color=ft.Colors.PURPLE_300),
                ft.Column([
                    ft.Text("Arcade Trip Hub", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Modo Offline - Sem Internet? Sem problema.", size=12, color=ft.Colors.GREY_400),
                ], spacing=2)
            ]),
            ft.Divider(color=ft.Colors.WHITE10),
            
            ft.Container(height=20),
            
            ft.GridView(
                expand=True,
                runs_count=2,
                max_extent=200,
                child_aspect_ratio=1.0,
                spacing=15,
                run_spacing=15,
                controls=[
                    self._create_game_card(
                        "Forca do Viajante", 
                        "Descubra palavras sobre viagens antes que seja tarde!",
                        ft.Icons.TEXT_FIELDS_ROUNDED, 
                        ft.Colors.ORANGE, 
                        lambda e: self._launch_game(HangmanGame(self.main_page, self._back_to_hub))
                    ),
                    self._create_game_card(
                        "Caça Palavras", 
                        "Encontre os destinos escondidos na grade.",
                        ft.Icons.GRID_ON_ROUNDED, 
                        ft.Colors.BLUE,
                        # ATIVADO: Agora chama o WordSearchGame
                        lambda e: self._launch_game(WordSearchGame(self.main_page, self._back_to_hub)) 
                    ),
                    self._create_game_card(
                        "Quiz Geográfico", 
                        "Você sabe onde fica este país?",
                        ft.Icons.PUBLIC, 
                        ft.Colors.GREEN, 
                        lambda e: self._show_unavailable("Em breve: Quiz")
                    ),
                    self._create_game_card(
                        "Paciência", 
                        "O clássico passatempo de cartas.",
                        ft.Icons.FILTER_FRAMES_ROUNDED, 
                        ft.Colors.RED, 
                        lambda e: self._show_unavailable("Requer lógica avançada")
                    ),
                ]
            )
        ])

    def _create_game_card(self, title, subtitle, icon, color, on_click):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=40, color=color),
                        padding=15,
                        bgcolor=ft.Colors.with_opacity(0.1, color),
                        border_radius=50,
                    ),
                    ft.Text(title, weight=ft.FontWeight.BOLD, size=16, text_align=ft.TextAlign.CENTER),
                    ft.Text(subtitle, size=11, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            bgcolor=ft.Colors.GREY_900,
            border=ft.border.all(1, ft.Colors.WHITE10),
            border_radius=15,
            ink=True,
            on_click=on_click,
            padding=15,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 5)
            )
        )

    def _launch_game(self, game_control):
        self.content = game_control
        self.update()

    def _back_to_hub(self):
        self.content = self.menu_content
        self.update()

    def _show_unavailable(self, msg):
        self.main_page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="grey")
        self.main_page.snack_bar.open = True
        self.main_page.update()