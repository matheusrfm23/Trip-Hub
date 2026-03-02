import flet as ft
import logging
import traceback
import asyncio

from src.core.logger import logger
from src.logic.auth_service import AuthService
from src.ui.views.login_view import LoginView
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.country_view import CountryView

class Router:
    PUBLIC_ROUTES = ["/login", "/error", "/logout"]

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.on_route_change = self._on_route_change_event
        self.page.on_view_pop = self._on_view_pop_event

    async def _on_route_change_event(self, e):
        logger.info(f"Evento de Rota Detectado: {e.route}")
        await self.route_change(e.route)

    async def _on_view_pop_event(self, e):
        if len(self.page.views) > 1:
            self.page.views.pop()
            top_view = self.page.views[-1]
            await self.page.push_route(top_view.route)

    async def route_change(self, route):
        logger.info(f"Processando navegação para: {route}")
        
        self.page.views.clear()
        
        try:
            if route == "/logout":
                self._perform_logout()
                self.page.views.append(LoginView(self.page))
                self.page.update()
                return

            if route not in self.PUBLIC_ROUTES:
                if not hasattr(self.page, "user_profile") or not self.page.user_profile:
                    logger.info("Sessão vazia. Tentando restaurar...")
                    
                    session_restored = await self._try_restore_session()
                    
                    if not session_restored:
                        logger.warning(f"Acesso negado à rota '{route}'.")
                        self.page.views.append(LoginView(self.page))
                        self.page.update()
                        return

            troute = ft.TemplateRoute(route)
            
            if route == "/login":
                if hasattr(self.page, "user_profile") and self.page.user_profile:
                     await self.page.push_route("/dashboard")
                     return
                self.page.views.append(LoginView(self.page))
            
            elif route == "/dashboard":
                self.page.views.append(DashboardView(self.page))
            
            elif troute.match("/country/:code"):
                self.page.views.append(CountryView(self.page, troute.code))
            
            elif route == "/error":
                 self._append_error_view("Erro genérico.")

            else:
                if hasattr(self.page, "user_profile") and self.page.user_profile:
                    await self.page.push_route("/dashboard")
                else:
                    await self.page.push_route("/login")

        except Exception as e:
            error_msg = traceback.format_exc()
            logger.critical(f"ERRO CRÍTICO NO ROTEADOR: {error_msg}")
            self._append_error_view(error_msg)
            
        self.page.update()

    async def _try_restore_session(self):
        try:
            if not hasattr(self.page, "client_storage") or self.page.client_storage is None:
                return False

            stored_user_id = self.page.client_storage.get("user_id")
            if not stored_user_id:
                return False
            
            user_profile = await AuthService.get_user_by_id(stored_user_id)
            if user_profile:
                self.page.user_profile = user_profile
                return True
            else:
                self.page.client_storage.remove("user_id")
                return False
        except Exception:
            return False

    def _perform_logout(self):
        if hasattr(self.page, "user_profile"):
            del self.page.user_profile
        try:
            if self.page.client_storage:
                self.page.client_storage.remove("user_id")
        except Exception as e:
            logger.error("Falha ao remover user_id do client_storage no logout.", exc_info=True)
            if hasattr(self.page, "session"):
                try:
                    self.page.session.clear()
                except Exception:
                    pass

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
                        ft.ElevatedButton("Reiniciar", on_click=lambda e: self.page.run_task(self.page.push_route, "/login"))
                    ], alignment="center", horizontal_alignment="center")
                ]
            )
        )