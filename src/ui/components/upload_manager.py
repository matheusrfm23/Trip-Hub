# ARQUIVO: src/ui/components/upload_manager.py
# CHANGE LOG:
# - Correção no tratamento do nome do arquivo pós-upload. Renomeia o arquivo limpo (sem acentos) 
#   de volta para o nome original na pasta "uploads" de forma invisível, garantindo que o 
#   PlaceModalManager consiga encontrar o arquivo exatamente pelo nome que ele espera.
# - A limpeza da lista 'picked_files' foi movida para depois de invocar o callback (on_complete).

import flet as ft
import re
import unicodedata
import os
from src.core.config import UPLOAD_ABS_PATH

class UploadManager:
    def __init__(self, page: ft.Page, on_upload_complete_callback, log_callback=print):
        self.page = page
        self.on_complete = on_upload_complete_callback
        self.log = log_callback
        self.picked_files = []
        self.sanitized_map = {}
        
        self.progress_bar = ft.ProgressBar(width=None, color="amber", bgcolor="#222222", value=0, visible=False)
        self.file_picker = ft.FilePicker(on_upload=self._on_upload_progress)

        self.btn_pick = ft.FilledButton("Selecionar Fotos", icon=ft.Icons.PHOTO_LIBRARY, on_click=self._pick_click)
        self.btn_upload = ft.FilledButton("Enviar", icon=ft.Icons.CLOUD_UPLOAD, on_click=self._upload_click, disabled=True, bgcolor=ft.Colors.BLUE_700)

    def get_ui(self):
        return ft.Column([
            ft.Row([self.file_picker], visible=False), 
            ft.Row([self.btn_pick, self.btn_upload], alignment=ft.MainAxisAlignment.CENTER),
            self.progress_bar
        ])

    def _sanitize_filename(self, filename):
        nfkd_form = unicodedata.normalize('NFKD', filename)
        filename = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        filename = filename.lower().replace(" ", "_")
        filename = re.sub(r'[^a-z0-9_.-]', '', filename)
        return filename

    def _on_upload_progress(self, e):
        if e.progress is None: return

        self.progress_bar.value = e.progress
        if e.progress >= 1.0:
            self.progress_bar.visible = False
            self.btn_upload.disabled = True
            self.btn_upload.text = "Enviar"
            
            # [WORKAROUND BACKEND] Restauramos os nomes originais físicos para o ModalManager encontrar
            for original_name, clean_name in self.sanitized_map.items():
                if original_name != clean_name:
                    clean_path = os.path.join(UPLOAD_ABS_PATH, clean_name)
                    original_path = os.path.join(UPLOAD_ABS_PATH, original_name)
                    if os.path.exists(clean_path):
                        if os.path.exists(original_path):
                            try: os.remove(original_path)
                            except: pass
                        try: os.rename(clean_path, original_path)
                        except: pass
            
            self.page.snack_bar = ft.SnackBar(ft.Text("Upload concluído com sucesso!"), bgcolor="green")
            self.page.snack_bar.open = True
            self.page.update()
            
            # [CORREÇÃO DE CALLBACK] Dispara o evento ANTES de limpar a lista
            if self.on_complete:
                self.on_complete() 
                
            self.picked_files = [] 
            self.sanitized_map = {}
            
        self.page.update()

    async def _pick_click(self, e):
        try: 
            if self.file_picker not in self.page.controls and self.file_picker.page is None:
                 return

            files = await self.file_picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.IMAGE
            )
            
            if files:
                self.picked_files = files
                self.btn_upload.disabled = False
                self.btn_upload.text = f"Enviar ({len(files)})"
                self.page.snack_bar = ft.SnackBar(ft.Text(f"{len(files)} fotos selecionadas"), bgcolor="blue")
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as ex:
            print(f"Erro ao selecionar: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text("Erro de conexão. Tente novamente."), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    async def _upload_click(self, e):
        if not self.picked_files: return
        
        self.btn_upload.disabled = True
        self.progress_bar.visible = True
        self.page.update()
        
        try:
            uploads = []
            self.sanitized_map = {}
            for f in self.picked_files:
                clean_name = self._sanitize_filename(f.name)
                self.sanitized_map[f.name] = clean_name
                
                upload_url = self.page.get_upload_url(clean_name, 600)
                
                uploads.append(
                    ft.FilePickerUploadFile(
                        name=f.name,
                        upload_url=upload_url,
                        method="PUT"
                    )
                )
            
            await self.file_picker.upload(files=uploads)
            
        except Exception as ex:
            print(f"Erro no upload: {ex}")
            self.progress_bar.visible = False
            self.btn_upload.disabled = False
            self.page.snack_bar = ft.SnackBar(ft.Text("Falha no envio. A conexão pode ter caído."), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()