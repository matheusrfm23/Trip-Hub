import flet as ft
import logging
import traceback
import asyncio

from src.logic.auth_service import AuthService
from src.ui.views.login_view import LoginView
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.country_view import CountryView

logger = logging.getLogger("TripHub.Router")

class Router:
    # Adicionei /logout para garantir a saída limpa
    PUBLIC_ROUTES = ["/login", "/error", "/logout"]

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.on_route_change = self._on_route_change_event
        self.page.on_view_pop = self._on_view_pop_event

    async def _on_route_change_event(self, e):
        logger.info(f"Evento de Rota Detectado: {e.route}")
        await self.route_change(e.route)

    def _on_view_pop_event(self, e):
        # [CORREÇÃO] Stack Navigation: Remove a view do topo e volta para a anterior
        if len(self.page.views) > 1:
            self.page.views.pop()
            top_view = self.page.views[-1]
            self.page.go(top_view.route) 
        else:
            # Se for a última view, redireciona para dashboard por segurança
            self.page.go("/dashboard")

    async def route_change(self, route):
        logger.info(f"Processando navegação para: {route}")
        
        # [CORREÇÃO] Removida a limpeza agressiva global self.page.views.clear()
        
        try:
            # === ROTA DE LOGOUT ===
            if route == "/logout":
                self._perform_logout()
                self.page.views.clear() # Limpa histórico para evitar voltar
                self.page.views.append(LoginView(self.page))
                self.page.update()
                return

            # === BLINDAGEM DE SESSÃO ===
            if route not in self.PUBLIC_ROUTES:
                if not hasattr(self.page, "user_profile") or not self.page.user_profile:
                    logger.info("Sessão vazia. Tentando restaurar...")
                    
                    session_restored = await self._try_restore_session()
                    
                    if not session_restored:
                        logger.warning(f"Acesso negado à rota '{route}'.")
                        
                        # Redireciona para login sem manter histórico da rota negada
                        self.page.views.clear()
                        self.page.views.append(LoginView(self.page))
                        self.page.update()
                        return

            # === ROTEAMENTO NORMAL (Stack Navigation) ===
            troute = ft.TemplateRoute(route)
            
            if route == "/login":
                if hasattr(self.page, "user_profile") and self.page.user_profile:
                     self.page.go("/dashboard")
                     return
                self.page.views.clear()
                self.page.views.append(LoginView(self.page))
            
            elif route == "/dashboard":
                self.page.views.clear()
                self.page.views.append(DashboardView(self.page))
            
            elif troute.match("/country/:code"):
                # [A MÁGICA] Garante que o Dashboard esteja na base da pilha
                # Isso permite que o botão "Voltar" do AppBar funcione e leve ao Dashboard
                self.page.views.clear()
                self.page.views.append(DashboardView(self.page))
                self.page.views.append(CountryView(self.page, troute.code))
            
            elif route == "/error":
                 self.page.views.clear()
                 self._append_error_view("Erro genérico.")

            else:
                # Rota 404 - Redirecionamento Inteligente
                if hasattr(self.page, "user_profile") and self.page.user_profile:
                    self.page.go("/dashboard")
                else:
                    self.page.go("/login")

        except Exception as e:
            error_msg = traceback.format_exc()
            logger.critical(f"ERRO CRÍTICO NO ROTEADOR: {error_msg}")
            self.page.views.clear()
            self._append_error_view(error_msg)
            
        self.page.update()

    async def _try_restore_session(self):
        """
        Tenta restaurar a sessão do usuário a partir do client_storage (Flet).
        Retorna True se sucesso, False caso contrário.
        """
        try:
            # [RECUPERAÇÃO ANTI-LIMBO]
            # Verifica se o storage está disponível e acessível
            if not hasattr(self.page, "client_storage") or self.page.client_storage is None:
                return False

            stored_user_id = self.page.client_storage.get("user_id")
            if not stored_user_id:
                return False
            
            # Busca perfil no disco usando o AuthService refatorado (stateless)
            user_profile = await AuthService.get_user_by_id(stored_user_id)
            if user_profile:
                self.page.user_profile = user_profile
                logger.info(f"Sessão restaurada para usuário: {user_profile['name']}")
                return True
            else:
                # Se o ID no storage for inválido (ex: usuário deletado), limpa.
                self.page.client_storage.remove("user_id")
                return False
        except Exception as e:
            logger.error(f"Erro ao restaurar sessão: {e}")
            return False

    def _perform_logout(self):
        if hasattr(self.page, "user_profile"):
            del self.page.user_profile
        try:
            if self.page.client_storage:
                self.page.client_storage.remove("user_id")
        except: pass

    def _append_error_view(self, msg):
        self.page.views.append(
            ft.View(
                route="/error",
                bgcolor=ft.Colors.RED_900,
                controls=[
                    ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=60, color=ft.Colors.WHITE),
                        ft.Text("Erro Crítico", size=24, weight="bold"),
                        ft.Text(str(msg), color=ft.Colors.WHITE30),
                        ft.ElevatedButton("Reiniciar", on_click=lambda _: self.page.go("/login"))
                    ], alignment="center", horizontal_alignment="center")
                ]
            )
        )
