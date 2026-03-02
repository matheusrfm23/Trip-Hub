import flet as ft
import asyncio
import time
from datetime import datetime
from src.logic.chat_service import ChatService
from src.core.logger import get_logger

logger = get_logger(__name__)

class ChatContent(ft.Container):
    def __init__(self, page: ft.Page, current_user, target_user, on_back):
        super().__init__(
            # SEM ALTURA FIXA AQUI - Vamos deixar o pai controlar ou usar expand
            expand=True, 
            padding=0, 
            bgcolor=ft.Colors.GREY_900 
        )
        
        self.page_ref = page
        self.user = current_user
        self.target = target_user
        self.on_back = on_back
        self.running = False
        
        # --- UI ELEMENTS ---
        self.msg_list = ft.Column(
            scroll=ft.ScrollMode.ALWAYS, 
            expand=True, 
            spacing=10,
            auto_scroll=True # Rola para baixo automaticamente
        )
        
        self.tf_input = ft.TextField(
            hint_text="Digite sua mensagem...", 
            border_radius=20, 
            filled=True, 
            bgcolor=ft.Colors.BLACK,
            expand=True,
            on_submit=self._send_message,
            text_size=14,
            multiline=False
        )
        
        self.btn_send = ft.IconButton(
            ft.Icons.SEND, 
            icon_color=ft.Colors.CYAN, 
            on_click=self._send_message
        )

        # Header do Chat
        header = ft.Container(
            padding=10, bgcolor=ft.Colors.BLUE_GREY_800,
            content=ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()),
                ft.CircleAvatar(
                    content=ft.Text(self.target["name"][:2].upper()), 
                    bgcolor=ft.Colors.CYAN_900, radius=18
                ),
                ft.Column([
                    ft.Text(self.target["name"], weight="bold", size=16),
                    ft.Text("Online", size=10, color=ft.Colors.GREEN_400) 
                ], spacing=0),
            ])
        )

        # Input Area (Rodapé fixo)
        input_area = ft.Container(
            padding=10, bgcolor=ft.Colors.BLUE_GREY_900,
            content=ft.Row([self.tf_input, self.btn_send])
        )

        # Layout Principal
        self.content = ft.Column([
            header,
            ft.Container(self.msg_list, padding=10, expand=True), 
            input_area
        ], spacing=0)

    def did_mount(self):
        print("Chat montado.")
        self.running = True
        self.page_ref.run_task(self._poll_messages)
        self.page_ref.run_task(self._safe_focus)

    async def _safe_focus(self):
        try:
            await self.tf_input.focus()
        except Exception as e:
            logger.warning(f"Failed to focus input field: {e}")

    def will_unmount(self):
        print("Chat desmontado.")
        self.running = False

    async def _poll_messages(self):
        while self.running:
            try:
                msgs = await ChatService.get_conversation(self.user["id"], self.target["id"])
                
                controls = []
                for m in msgs:
                    controls.append(self._build_bubble(m))
                
                if len(self.msg_list.controls) != len(controls):
                    self.msg_list.controls = controls
                    self.msg_list.update()
                
            except Exception as e:
                print(f"Erro no loop do chat: {e}")
            
            await asyncio.sleep(1.5) 

    async def _send_message(self, e):
        text = self.tf_input.value
        if not text: return
        
        self.tf_input.value = ""
        self.tf_input.update()
        
        success = await ChatService.send_message(self.user["id"], self.target["id"], text)
        if success:
            await self._poll_messages() 
        else:
            print("Falha ao enviar mensagem.")

    def _build_bubble(self, msg):
        is_me = str(msg["sender_id"]) == str(self.user["id"])
        
        try:
            dt = datetime.fromtimestamp(float(msg["timestamp"]))
            time_str = dt.strftime("%H:%M")
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"Failed to parse timestamp {msg.get('timestamp')}: {e}")
            time_str = "--:--"

        return ft.Row(
            alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    padding=10,
                    border_radius=ft.border_radius.only(
                        top_left=12, top_right=12,
                        bottom_left=0 if not is_me else 12,
                        bottom_right=0 if is_me else 12
                    ),
                    bgcolor=ft.Colors.CYAN_900 if is_me else ft.Colors.GREY_800,
                    content=ft.Column([
                        ft.Text(msg["content"], size=15, color=ft.Colors.WHITE, width=200, no_wrap=False), 
                        ft.Row([
                            ft.Text(time_str, size=10, color=ft.Colors.WHITE54),
                            ft.Icon(ft.Icons.DONE_ALL, size=14, color=ft.Colors.BLUE_200 if msg["is_read"] else ft.Colors.GREY) if is_me else ft.Container()
                        ], alignment=ft.MainAxisAlignment.END, spacing=2, run_spacing=0)
                    ], spacing=2)
                )
            ]
        )