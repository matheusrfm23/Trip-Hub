import flet as ft
from datetime import datetime, timedelta
from src.ui.components.flights.utils import calculate_trip_stats

class FlightCardManager:
    def __init__(self, page, user, on_edit, on_delete, on_clone, on_qr):
        self.page = page
        self.user = user
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_clone = on_clone
        self.on_qr = on_qr

    def create_card(self, data):
        owner = data.get("user_name", "Desconhecido")
        is_mine = str(data.get("user_id")) == str(self.user["id"])
        segments = data.get("segments", [])
        
        trip_title = data.get("trip_title", "")
        ticket_num = data.get("ticket_number", "")
        
        if not segments: return ft.Container()

        stats = calculate_trip_stats(segments)
        
        # Cor da borda
        border_color = ft.Colors.GREY_700
        if is_mine: border_color = ft.Colors.CYAN
        if stats and stats["status"] in ["flying", "connection"]: 
            border_color = stats["status_color"]

        # Barra de progresso
        progress_bar = ft.Container()
        if stats and stats["progress"] > 0 and stats["progress"] < 1:
            progress_bar = ft.ProgressBar(value=stats["progress"], color=stats["status_color"], bgcolor=ft.Colors.GREY_800, height=4)

        # --- Segmentos ---
        segment_controls = []
        for i, seg in enumerate(segments):
            is_last = i == len(segments) - 1
            
            # Conexão
            connection_info = ft.Container()
            conn_note = seg.get("connection_note", "")
            if not is_last and len(segments) > 1:
                next_seg = segments[i+1]
                wait_time = "--"
                try:
                    # Cálculo simples de tempo de conexão
                    t1 = datetime.strptime(f"{seg.get('date')} {seg.get('arr_time')}", "%d/%m/%Y %H:%M")
                    # Ajuste virada de dia se necessário (simplificado)
                    t2 = datetime.strptime(f"{next_seg.get('date')} {next_seg.get('time')}", "%d/%m/%Y %H:%M")
                    if t2 < t1: t2 += timedelta(days=1) 
                    diff = t2 - t1
                    wait_time = f"{diff.seconds//3600}h {(diff.seconds%3600)//60}m"
                except: pass

                conn_text = f"Conexão: {wait_time}"
                if conn_note: conn_text += f" • {conn_note}"
                
                connection_info = ft.Container(
                    bgcolor=ft.Colors.BLACK45, padding=5, border_radius=5, margin=ft.margin.symmetric(vertical=5),
                    content=ft.Row([ft.Icon(ft.Icons.ACCESS_TIME, size=12, color=ft.Colors.YELLOW), ft.Text(conn_text, size=11, color=ft.Colors.YELLOW, weight="bold")], alignment="center")
                )

            # QR Code e Portão
            has_qr = bool(seg.get("raw_code"))
            qr_icon_color = ft.Colors.CYAN if has_qr else ft.Colors.GREY_600
            gate_info = seg.get("gate", "")
            gate_display = ft.Text(f"Portão: {gate_info}", color=ft.Colors.AMBER, weight="bold", size=12) if gate_info else ft.Container()

            # Linha do Segmento
            row = ft.Row([
                ft.Column([
                    ft.Text(seg.get("origin", "AAA"), weight="bold", color=ft.Colors.WHITE),
                    ft.Container(width=2, height=35, bgcolor=ft.Colors.GREY_700, margin=ft.margin.symmetric(horizontal=10)),
                    ft.Text(seg.get("dest", "BBB"), weight="bold", color=ft.Colors.WHITE) if is_last else ft.Container()
                ], spacing=0, alignment="center", horizontal_alignment="center"),
                
                ft.Column([
                    ft.Row([
                        ft.Text(f"{seg.get('airline')} {seg.get('code')}", weight="bold", size=16),
                        ft.Container(padding=ft.padding.symmetric(horizontal=6, vertical=2), bgcolor=ft.Colors.BLUE_GREY_800, border_radius=4, content=ft.Text(seg.get("date"), size=10))
                    ]),
                    ft.Row([
                        ft.Text(seg.get("time", "??:??"), size=14, color=ft.Colors.WHITE, weight="bold"),
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=12, color=ft.Colors.GREY),
                        ft.Text(seg.get("arr_time", "??:??"), size=14, color=ft.Colors.WHITE, weight="bold"),
                    ]),
                    ft.Row([ft.Text(f"Assento: {seg.get('seat')}", color=ft.Colors.ORANGE, size=12), ft.Container(width=10), gate_display])
                ], expand=True),
                
                # --- TRAVA DE PRIVACIDADE ---
                ft.IconButton(ft.Icons.QR_CODE, icon_color=qr_icon_color, visible=is_mine, on_click=lambda e, s=seg: self.on_qr(s, owner))
            ], alignment="start", vertical_alignment="start")
            
            segment_controls.append(row)
            if connection_info.content: segment_controls.append(connection_info)
            if not is_last and not connection_info.content: segment_controls.append(ft.Divider(height=10, color=ft.Colors.GREY_800))

        clone_btn = ft.Container()
        if not is_mine:
            clone_btn = ft.Container(margin=ft.margin.only(top=10), content=ft.OutlinedButton("CLONAR ESTE VOO", icon=ft.Icons.CONTENT_COPY, style=ft.ButtonStyle(color=ft.Colors.CYAN, side=ft.BorderSide(1, ft.Colors.CYAN)), on_click=lambda e: self.on_clone(data)))

        # === CABEÇALHO SUPER COMPACTO ===
        header_items = []
        
        # 1. Status (Topo)
        header_items.append(
            ft.Row([
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=1), 
                    bgcolor=stats["status_color"] if stats else ft.Colors.GREY, 
                    border_radius=5,
                    content=ft.Text(stats["status_text"] if stats else "Info", color=ft.Colors.BLACK, size=11, weight="bold")
                ),
                ft.Text(f"Total: {stats['duration_str']}" if stats else "", size=11, color=ft.Colors.WHITE, italic=True)
            ], alignment="spaceBetween")
        )

        # 2. Título (Ex: CNF -> IGU)
        if trip_title:
            header_items.append(ft.Text(trip_title, size=14, weight="bold", color=ft.Colors.CYAN_100))
        
        # 3. Bilhete
        if ticket_num:
             header_items.append(ft.Text(f"Bilhete: {ticket_num}", size=10, color=ft.Colors.GREY_400))

        # 4. Usuário (COLADO LOGO ABAIXO DO BILHETE)
        # Usamos apenas um Row simples sem padding extra
        header_items.append(
            ft.Row([
                ft.Icon(ft.Icons.PERSON, size=14, color=border_color),
                ft.Text(owner.upper(), size=12, color=border_color, weight="bold"),
                ft.Container(expand=True), # Empurra botões pra direita
                ft.Row([
                    ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE_400, icon_size=18, on_click=lambda e: self.on_edit(data)),
                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, icon_size=18, on_click=lambda e: self.on_delete(data.get("id")))
                ], spacing=0, visible=is_mine) 
            ])
        )

        return ft.Container(
            bgcolor=ft.Colors.GREY_900, border_radius=12, padding=15,
            border=ft.border.only(left=ft.BorderSide(4, border_color)),
            content=ft.Column([
                # Spacing=1 cola os textos verticalmente
                ft.Column(header_items, spacing=1),
                
                ft.Container(height=5),
                progress_bar,
                ft.Divider(height=10, color=ft.Colors.GREY_800), # Separador para os segmentos
                *segment_controls,
                clone_btn
            ], spacing=2)
        )