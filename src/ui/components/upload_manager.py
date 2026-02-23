# ARQUIVO: src/ui/components/upload_manager.py
import flet as ft
import re
import unicodedata
from src.core.config import UPLOAD_ABS_PATH

class UploadManager:
    def __init__(self, page: ft.Page, on_upload_complete_callback, log_callback=print):
        self.page = page
        self.on_complete = on_upload_complete_callback
        self.log = log_callback
        self.picked_files = []
        
        # UI Elements
        self.progress_bar = ft.ProgressBar(width=None, color="amber", bgcolor="#222222", value=0, visible=False)
        
        # Inicializa o FilePicker
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
        """
        Remove acentos, espaços e caracteres especiais para evitar erro 
        'Response content longer than Content-Length' no servidor.
        Ex: 'Foto da Praia!.jpg' -> 'foto_da_praia.jpg'
        """
        # 1. Normaliza unicode (separa acentos das letras)
        nfkd_form = unicodedata.normalize('NFKD', filename)
        # 2. Mantém apenas caracteres ASCII (remove acentos)
        filename = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        # 3. Converte para minúsculas
        filename = filename.lower()
        # 4. Substitui espaços por underscores
        filename = filename.replace(" ", "_")
        # 5. Remove tudo que não for letra, número, underline, traço ou ponto
        filename = re.sub(r'[^a-z0-9_.-]', '', filename)
        return filename

    def _on_upload_progress(self, e):
        # Proteção contra valores nulos durante falhas de rede
        if e.progress is None: return

        self.progress_bar.value = e.progress
        if e.progress >= 1.0:
            self.progress_bar.visible = False
            self.picked_files = [] 
            self.btn_upload.disabled = True
            self.btn_upload.text = "Enviar"
            
            # Feedback visual de sucesso
            self.page.snack_bar = ft.SnackBar(ft.Text("Upload concluído com sucesso!"), bgcolor="green")
            self.page.snack_bar.open = True
            self.page.update()
            
            if self.on_complete:
                self.on_complete() 
        self.page.update()

    async def _pick_click(self, e):
        try: 
            if self.file_picker not in self.page.controls and self.file_picker.page is None:
                 return

            # OTIMIZAÇÃO: file_type=IMAGE força galeria no mobile
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
            else:
                pass # Usuário cancelou
                
        except Exception as ex:
            print(f"Erro ao selecionar: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text("Erro de conexão. Tente selecionar mais rápido."), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    async def _upload_click(self, e):
        if not self.picked_files: return
        
        self.btn_upload.disabled = True
        self.progress_bar.visible = True
        self.page.update()
        
        try:
            uploads = []
            for f in self.picked_files:
                # APLICA A SANITIZAÇÃO AQUI
                clean_name = self._sanitize_filename(f.name)
                
                # Gera URL com o nome limpo
                upload_url = self.page.get_upload_url(clean_name, 600)
                
                uploads.append(
                    ft.FilePickerUploadFile(
                        name=f.name, # Nome original para o picker saber qual arquivo pegar do disco local
                        upload_url=upload_url, # URL de destino (já contém o nome limpo)
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