import flet as ft
import time
import asyncio
import os
import shutil
from src.ui.components.common.image_carousel import ImageCarousel
from src.ui.components.upload_manager import UploadManager
from src.ui.components.gallery_viewer import GalleryViewer
from src.core.config import UPLOAD_ABS_PATH, ASSETS_DIR
import glob

class PlaceModalManager:
    def __init__(self, page: ft.Page, on_data_change):
        self.page = page
        self.on_data_change = on_data_change 
        self.is_admin = getattr(page, 'user_profile', {}).get("role") == "ADMIN"
        
        self.target_item_id = None
        self.current_modal = None
        
        # --- Modais Globais ---
        self.zoom_img = ft.Image(src="", fit="contain", expand=True)
        self.zoom_dialog = ft.AlertDialog(
            content_padding=0, bgcolor=ft.Colors.BLACK,
            content=ft.Container(content=self.zoom_img, alignment=ft.Alignment(0,0), expand=True),
            actions=[ft.TextButton("Fechar", on_click=lambda e: self.close_modal(self.zoom_dialog))]
        )
        
        self.photo_dialog = ft.AlertDialog(title=ft.Text("Fotos"), content=ft.Container(), actions=[])
        self._init_photo_manager()
        
        # Modal de Cópia Manual (Fallback Essencial)
        self.copy_field = ft.TextField(read_only=True, expand=True, text_size=14, border_color=ft.Colors.CYAN)
        self.copy_dialog = ft.AlertDialog(
            title=ft.Text("Copiar Endereço"),
            content=ft.Container(
                content=self.copy_field, 
                height=60, 
                padding=5
            ),
            actions=[ft.TextButton("OK", on_click=lambda e: self.close_modal(self.copy_dialog))],
            actions_alignment="center"
        )

        # Garante que todos estejam no overlay
        for m in [self.zoom_dialog, self.photo_dialog, self.copy_dialog]:
            if m not in self.page.overlay: self.page.overlay.append(m)

    def open_modal(self, modal):
        if modal not in self.page.overlay: self.page.overlay.append(modal)
        modal.open = True
        self.page.update()

    def close_modal(self, modal):
        modal.open = False
        self.page.update()

    # --- MAPS FIX (BLINDADO) ---
    async def safe_launch_url(self, url):
        print(f"DEBUG: Tentando abrir mapa: {url}")
        if not url: 
            self._snack("Link indisponível", ft.Colors.ORANGE)
            return
        
        target = url.strip()
        # Corrige links sem protocolo
        if not target.lower().startswith("http"): 
            target = "https://" + target
            
        try:
            # Tenta forçar NOVA ABA usando parâmetro nativo
            await self.page.launch_url(target, web_window_name="_blank")
        except TypeError:
            # Se a versão for muito antiga e não aceitar '_blank', tenta normal
            print("DEBUG: Versão antiga detectada, abrindo modo padrão.")
            try:
                await self.page.launch_url(target)
            except Exception as e:
                self._snack(f"Erro ao abrir: {e}", ft.Colors.RED)
        except Exception as e:
            print(f"Erro Crítico Maps: {e}")
            self._snack("Erro ao abrir link", ft.Colors.RED)

    # --- CLIPBOARD FIX (SEM JAVASCRIPT) ---
    async def smart_copy(self, text):
        if not text: return
        print(f"DEBUG: Copiando '{text}'")
        
        success = False
        # Tenta método nativo do Flet (funciona na maioria das versões)
        try:
            if hasattr(self.page, "set_clipboard"):
                await self.page.set_clipboard(text)
                success = True
            elif hasattr(self.page, "clipboard"):
                await self.page.clipboard.set_data(text)
                success = True
        except: 
            pass

        if success:
            self._snack("Copiado!", ft.Colors.GREEN)
        else:
            # Fallback Visual: Mostra o modal para o usuário copiar
            print("DEBUG: Falha na cópia automática. Abrindo modal manual.")
            self.copy_field.value = text
            self.open_modal(self.copy_dialog)
            try: await self.copy_field.focus()
            except: pass
            self._snack("Copie manualmente.", ft.Colors.BLUE)

    # --- DETALHES ---
    def show_details(self, item, on_edit_click, on_delete_click):
        carousel = ImageCarousel(
            images=self._get_images(item["id"]),
            is_admin=self.is_admin,
            height=280,
            on_zoom=self.open_zoom,
            on_delete_photo=lambda path: self.page.run_task(self.delete_photo, path)
        )
        
        admin_row = ft.Row(visible=False)
        if self.is_admin:
            admin_row.visible = True
            admin_row.controls = [
                ft.TextButton("Add Foto", icon=ft.Icons.ADD_A_PHOTO, on_click=lambda _: self.open_photo_manager(item["id"])),
                ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE, on_click=lambda e: on_edit_click(item)),
                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e: on_delete_click(item))
            ]

        try: p = float(item.get("price", 0) or 0); txt_p = f"R$ {p:,.2f}"
        except: txt_p = "R$ --"

        # Wrapper para garantir execução Assíncrona no clique
        def create_action_btn(icon, text, color, async_func, arg):
            async def _handle_click(e):
                await async_func(arg)

            return ft.Container(
                content=ft.Row([ft.Icon(icon, color=ft.Colors.WHITE, size=18), ft.Text(text, color=ft.Colors.WHITE)], alignment="center"),
                bgcolor=color, padding=10, border_radius=8, expand=True, ink=True, 
                on_click=_handle_click
            )

        content = ft.Column([
            carousel,
            ft.Container(height=10),
            admin_row,
            ft.Row([
                ft.Text(item.get("name", ""), size=22, weight="bold", expand=True),
                ft.Container(content=ft.Text(txt_p, color=ft.Colors.WHITE, weight="bold"), bgcolor=ft.Colors.GREEN_700, padding=8, border_radius=8)
            ]),
            ft.Divider(),
            ft.Text(item.get("address", ""), size=14, selectable=True),
            ft.Container(height=10),
            ft.Text("Sobre:", weight="bold", color=ft.Colors.GREY_500),
            ft.Text(item.get("description", "Sem descrição.")),
            ft.Divider(),
            ft.Row([
                # Botões seguros
                create_action_btn(ft.Icons.MAP, "Mapa", ft.Colors.BLUE_900, self.safe_launch_url, item.get("maps_link")),
                ft.Container(width=10),
                create_action_btn(ft.Icons.COPY, "Copiar", ft.Colors.GREY_800, self.smart_copy, item.get("address"))
            ])
        ], scroll=ft.ScrollMode.AUTO)

        self.current_modal = ft.AlertDialog(
            content=ft.Container(content=content, width=450, height=650),
            actions=[ft.TextButton("Fechar", on_click=lambda e: self.close_modal(self.current_modal))]
        )
        self.open_modal(self.current_modal)

    # --- ZOOM & FOTOS (Lógica Mantida) ---
    def open_zoom(self, src): self.zoom_img.src = src; self.open_modal(self.zoom_dialog)
    
    def _init_photo_manager(self):
        self.gv = GalleryViewer(self.page, on_file_click=self._on_photo_selected)
        self.um = UploadManager(self.page, on_upload_complete_callback=self.gv.refresh)
        self.photo_dialog.content = ft.Container(width=500, height=500, content=ft.Column([
            ft.Text("Gerenciar", weight="bold"), self.um.get_ui(), ft.Divider(), self.gv.get_ui()
        ]))
        self.photo_dialog.actions = [ft.TextButton("Fechar", on_click=lambda e: self.close_modal(self.photo_dialog))]

    def open_photo_manager(self, item_id):
        self.target_item_id = item_id; self.gv.refresh()
        if self.current_modal and self.current_modal.open: self.close_modal(self.current_modal)
        self.open_modal(self.photo_dialog)

    def _on_photo_selected(self, filename):
        if not self.target_item_id: return
        try:
            src = os.path.join(UPLOAD_ABS_PATH, filename)
            dest = os.path.join(ASSETS_DIR, "images", f"{self.target_item_id}_{int(time.time())}{os.path.splitext(filename)[1]}")
            shutil.copy(src, dest); self.close_modal(self.photo_dialog); self.on_data_change() 
        except Exception as e: print(f"Erro: {e}")

    async def delete_photo(self, path):
        try:
            filename = path.split("/")[-1].split("?")[0]
            abs_path = os.path.join(ASSETS_DIR, "images", filename)
            if os.path.exists(abs_path):
                for _ in range(3):
                    try: os.remove(abs_path); break
                    except: await asyncio.sleep(0.5)
                self.on_data_change()
                if self.current_modal: self.close_modal(self.current_modal)
        except: pass

    def _get_images(self, item_id):
        files = glob.glob(os.path.join(ASSETS_DIR, "images", f"{item_id}_*")) + glob.glob(os.path.join(ASSETS_DIR, "images", f"{item_id}.jpg"))
        return [f"/images/{os.path.basename(f)}?t={time.time()}" for f in sorted(files)]

    def _snack(self, msg, color):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color); self.page.snack_bar.open = True; self.page.update()