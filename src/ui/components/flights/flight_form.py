import flet as ft
import copy
from src.logic.flight_service import FlightService

class FlightFormManager:
    def __init__(self, page: ft.Page, user, on_save_callback):
        self.page = page
        self.user = user
        self.on_save_callback = on_save_callback
        
        self.tf_trip_title = ft.TextField(label="Título da Viagem", hint_text="Ex: CNF -> IGU", expand=True)
        self.tf_ticket = ft.TextField(label="Nº Bilhete/Reserva", hint_text="XYZ123", width=150)
        
        self.segments_container = ft.Column(spacing=20)
        self.current_segments = []
        self.editing_id = None
        self.editing_type = None

        self.dialog = ft.AlertDialog(
            title=ft.Text("Gerenciar Voo"),
            content=ft.Container(width=500, height=600,
                content=ft.Column([
                    ft.Row([self.tf_trip_title, self.tf_ticket]),
                    ft.Divider(),
                    self.segments_container,
                    ft.Container(height=10),
                    ft.OutlinedButton("Adicionar Conexão", icon=ft.Icons.ADD_LINK, on_click=lambda e: self._add_segment_form())
                ], scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._close),
                ft.ElevatedButton("Salvar Tudo", bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, on_click=self._save_data)
            ]
        )

    def open(self, type_key=None, flight_data=None, is_cloning=False):
        self.segments_container.controls.clear()
        self.current_segments = []
        self.editing_id = flight_data.get("id") if flight_data and not is_cloning else None
        self.editing_type = type_key

        if flight_data:
            self.editing_type = flight_data.get("type")
            title = f"Editar Voo ({self.editing_type.title()})" if not is_cloning else f"Clonar Voo ({self.editing_type.title()})"
            self.dialog.title.value = title
            self.tf_trip_title.value = flight_data.get("trip_title", "")
            self.tf_ticket.value = flight_data.get("ticket_number", "")

            loaded_segs = flight_data.get("segments", [])
            if not loaded_segs:
                loaded_segs = [{k: flight_data.get(k, "") for k in ["airline", "code", "origin", "dest", "date", "time", "seat", "raw_code"]}]
            
            for s in loaded_segs: self._add_segment_form(s)
        else:
            self.dialog.title.value = f"Adicionar Voo ({type_key.title()})"
            self.tf_trip_title.value = ""
            self.tf_ticket.value = ""
            self._add_segment_form()

        if self.dialog not in self.page.overlay: self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()

    def _close(self, e):
        self.dialog.open = False
        self.page.update()

    def _format_date(self, e):
        text = "".join(c for c in e.control.value if c.isdigit())
        out = ""
        if len(text) > 0: out += text[:2]
        if len(text) >= 3: out += "/" + text[2:4]
        if len(text) >= 5: out += "/" + text[4:8]
        e.control.value = out
        e.control.update()

    def _format_time(self, e):
        text = "".join(c for c in e.control.value if c.isdigit())
        out = ""
        if len(text) > 0: out += text[:2]
        if len(text) >= 3: out += ":" + text[2:4]
        e.control.value = out
        e.control.update()

    def _add_segment_form(self, data=None):
        if data is None: data = {}
        
        airline = ft.TextField(label="Cia Aérea", hint_text="Latam", value=data.get("airline", ""), expand=1)
        code = ft.TextField(label="Nº Voo", hint_text="LA3044", value=data.get("code", ""), expand=1)
        origin = ft.TextField(label="Origem", hint_text="GRU", value=data.get("origin", ""), expand=1, text_align="center")
        dest = ft.TextField(label="Destino", hint_text="GIG", value=data.get("dest", ""), expand=1, text_align="center")
        
        date = ft.TextField(label="Data Saída", hint_text="DD/MM/AAAA", value=data.get("date", ""), expand=1, on_change=self._format_date, max_length=10, keyboard_type=ft.KeyboardType.NUMBER)
        time = ft.TextField(label="Hora Saída", hint_text="HH:MM", value=data.get("time", ""), expand=1, on_change=self._format_time, max_length=5, keyboard_type=ft.KeyboardType.NUMBER)
        arr_time = ft.TextField(label="Chegada", hint_text="HH:MM", value=data.get("arr_time", ""), expand=1, on_change=self._format_time, max_length=5, keyboard_type=ft.KeyboardType.NUMBER)
        
        seat = ft.TextField(label="Assento", hint_text="12F", value=data.get("seat", ""), width=100)
        gate = ft.TextField(label="Portão", hint_text="B12", value=data.get("gate", ""), width=100)
        conn_note = ft.TextField(label="Obs. Conexão (Opcional)", hint_text="Ex: Parada em VCP", value=data.get("connection_note", ""), text_size=12)
        raw_code = ft.TextField(label="Token QR Code (Oficial)", value=data.get("raw_code", ""), multiline=True, min_lines=2, text_size=12, hint_text="Cole o código do QR da GOL aqui")

        def remove_me(e):
            if len(self.current_segments) > 1:
                self.segments_container.controls.remove(segment_row)
                self.current_segments.remove(form_ref)
                self.dialog.update()

        remove_btn = ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED, tooltip="Remover Trecho", on_click=remove_me)

        segment_row = ft.Container(
            padding=15, border=ft.border.all(1, ft.Colors.GREY_800), border_radius=8, bgcolor=ft.Colors.BLACK26,
            content=ft.Column([
                ft.Row([ft.Text(f"Trecho de Viagem", weight="bold", color=ft.Colors.CYAN), remove_btn], alignment="spaceBetween"),
                ft.Row([airline, code], spacing=10),
                ft.Container(bgcolor=ft.Colors.BLACK12, padding=10, border_radius=8, content=ft.Row([origin, ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY), dest], alignment="center")),
                ft.Row([date, time, arr_time], spacing=10),
                ft.Row([seat, gate], spacing=10),
                conn_note,
                raw_code
            ], spacing=12)
        )
        
        form_ref = {
            "ui": segment_row,
            "fields": {
                "airline": airline, "code": code, "origin": origin, "dest": dest,
                "date": date, "time": time, "arr_time": arr_time,
                "seat": seat, "gate": gate, "connection_note": conn_note, "raw_code": raw_code
            }
        }
        self.current_segments.append(form_ref)
        self.segments_container.controls.append(segment_row)
        if self.dialog.open: self.dialog.update()

    async def _save_data(self, e):
        segments_data = []
        for seg in self.current_segments:
            f = seg["fields"]
            if not f["code"].value:
                f["code"].error_text = "*"
                self.dialog.update()
                return
            
            segments_data.append({
                "airline": f["airline"].value,
                "code": f["code"].value,
                "origin": f["origin"].value.upper(),
                "dest": f["dest"].value.upper(),
                "date": f["date"].value,
                "time": f["time"].value,
                "arr_time": f["arr_time"].value,
                "seat": f["seat"].value,
                "gate": f["gate"].value,
                "connection_note": f["connection_note"].value,
                "raw_code": f["raw_code"].value
            })

        final_data = {
            "type": self.editing_type,
            "user_id": self.user["id"],
            "user_name": self.user["name"],
            "trip_title": self.tf_trip_title.value,
            "ticket_number": self.tf_ticket.value,
            "segments": segments_data
        }

        self.dialog.open = False
        self.page.update()
        
        if self.editing_id: await FlightService.update_flight(self.editing_id, final_data)
        else: await FlightService.add_flight(final_data)
        
        if self.on_save_callback: await self.on_save_callback()