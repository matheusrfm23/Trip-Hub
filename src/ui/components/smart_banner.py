import flet as ft
import asyncio
import webbrowser
from datetime import datetime
from src.logic.banner_service import BannerService

class SmartBanner(ft.Container):
    # --- TEMAS ---
    THEMES = {
        "Ocean": [ft.Colors.BLUE_900, ft.Colors.CYAN_800],
        "Sunset": [ft.Colors.DEEP_ORANGE_900, ft.Colors.PURPLE_900],
        "Forest": [ft.Colors.GREEN_900, ft.Colors.TEAL_800],
        "Midnight": [ft.Colors.BLACK, ft.Colors.BLUE_GREY_900],
        "Aurora": [ft.Colors.TEAL_900, ft.Colors.PURPLE_900],
        "Mars": [ft.Colors.RED_900, ft.Colors.ORANGE_900],
    }

    DYNAMIC_PALETTE = {
        "day": [ft.Colors.BLUE_600, ft.Colors.CYAN_400],
        "night": [ft.Colors.INDIGO_900, ft.Colors.BLACK],
    }

    def __init__(self, page: ft.Page, user=None):
        super().__init__(
            border_radius=20, padding=20, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK45, offset=ft.Offset(0, 8)),
            animate=ft.Animation(800, ft.AnimationCurve.EASE_OUT),
        )
        self.page_ref = page
        self.user = user if user else getattr(page, 'user_profile', {})
        self.is_admin = self.user.get("role") == "ADMIN"
        self.running = True
        self.current_state = "LOADING"
        self.marquee_offset = 0
        self.admin_dialog = None
        self.weather_dialog = None
        self.track_width = 300 
        self.content = self._build_skeleton()
        
        # GPS Safe Check
        self.geolocator = None
        if hasattr(ft, "Geolocator"):
            self.geolocator = ft.Geolocator(
                on_position=self._on_gps_position,
                on_error=self._on_gps_error
            )
            try: self.page_ref.overlay.append(self.geolocator)
            except: pass

    def did_mount(self):
        self.running = True
        self.page_ref.run_task(self._main_loop)

    def will_unmount(self):
        self.running = False

    async def _main_loop(self):
        while self.running:
            try:
                data = await BannerService.get_oracle_data(self.user.get("id"))
                self.config = data.get("config", {})
                self.full_data = data
                self._apply_theme()
                
                new_state = data.get("state", "PLANNING")
                if new_state != self.current_state or getattr(self, "force_refresh", False):
                    self.current_state = new_state
                    self.force_refresh = False
                    
                    if new_state == "MANUAL":
                        self.content = self._build_manual_ui(data)
                        self.page_ref.run_task(self._animate_marquee)
                    elif new_state == "TIMER":
                        self.content = self._build_timer_ui(data)
                    else:
                        self.content = self._build_dashboard_ui(data)
                    self.update()
                
                if new_state not in ["MANUAL", "TIMER"]:
                    self._update_realtime_values(data)
            except Exception as e:
                pass
            await asyncio.sleep(1)

    # --- UI ---
    def _build_skeleton(self):
        return ft.Container(height=200, bgcolor=ft.Colors.WHITE10, alignment=ft.Alignment(0,0), content=ft.ProgressRing(color=ft.Colors.CYAN_200))

    def _build_dashboard_ui(self, data):
        cfg = self.config
        try: w = getattr(self.page_ref, "window_width", 400) or 400
        except: w = 400
        is_mobile = w < 600
        self.track_width = min(w - 60, 600)
        
        dest_name = cfg.get("target_location", {}).get("name", "Destino")
        
        header = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.FLIGHT_TAKEOFF, size=16, color="white70"),
                    ft.Text(f"RUMO A {dest_name.upper()}", weight="bold", size=11, color="white"),
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=10, color="white30")
                ], spacing=5),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.WHITE10, border_radius=8,
                on_click=self._open_google_maps, ink=True, tooltip="Abrir Mapa"
            ),
            self._build_settings_btn()
        ], alignment="spaceBetween")

        tsize = 32 if is_mobile else 42
        self.txt_timer = ft.Text("...", size=tsize, weight="bold", color="white", font_family="monospace", text_align="center")
        
        # TIMELINE COMPACTA
        timeline_section = ft.Container()
        if cfg.get("show_timeline", True):
            track = ft.Container(height=3, bgcolor=ft.Colors.WHITE12, border_radius=3, width=self.track_width)
            self.progress_bar = ft.Container(height=3, bgcolor=ft.Colors.CYAN_200, border_radius=3, width=0)
            self.progress_icon = ft.Container(content=ft.Icon(ft.Icons.AIRPLANEMODE_ACTIVE, size=14, color=ft.Colors.CYAN_100, rotate=ft.Rotate(1.57)), left=0, top=-6)
            timeline_section = ft.Container(
                content=ft.Stack([track, self.progress_bar, self.progress_icon], height=16, width=self.track_width),
                alignment=ft.Alignment(0,0), margin=ft.margin.only(top=10, bottom=10)
            )

        # WIDGETS (3 LINHAS CADA)
        widgets_content = []
        if cfg.get("show_weather", True):
            w = data.get("weather", {})
            try: code = int(w.get("code") or 0)
            except: code = 0
            widgets_content.append(self._glass_card(
                ft.Row([
                    ft.Icon(self._get_weather_icon(code, w.get("is_day", 1)), color="white", size=24),
                    ft.Column([
                        ft.Text(f"{w.get('temp', '--')}°C", weight="bold", size=12, color="white"),
                        ft.Text(str(w.get("desc", "--"))[:15], size=10, color="white70", no_wrap=True),
                        ft.Text(f"Chuva: {w.get('rain_prob', 0)}%", size=10, color="white70")
                    ], spacing=0, alignment="center")
                ], spacing=10, alignment="center"), 
                expand=True, on_click=self._open_weather_details, ink=True, tooltip="Previsão"
            ))
            
        if cfg.get("show_currency", True):
            fin = data.get("finance", {})
            icon_color = ft.Colors.GREEN_400 if data.get("alert_active") else ft.Colors.WHITE54
            widgets_content.append(self._glass_card(
                ft.Row([
                    ft.Icon(ft.Icons.CURRENCY_EXCHANGE, color=icon_color, size=24),
                    ft.Column([
                        ft.Text(f"USD {fin.get('usd', 0.0):.2f}", weight="bold", size=12, color="white"),
                        ft.Text(f"Blue {fin.get('blue', 0.0):.0f}", size=10, color="white70"),
                        ft.Text(f"PYG {fin.get('pyg', 0.0):.0f}", size=10, color="white70") 
                    ], spacing=0, alignment="center")
                ], spacing=10, alignment="center"),
                expand=True, on_click=self._open_currency_converter, ink=True, tooltip="Conversor"
            ))
            
        widgets_row = ft.Row(widgets_content, spacing=10) if widgets_content else ft.Container()

        advice_section = ft.Container()
        if cfg.get("show_advice", True):
            adv = data.get("advice", {})
            color_map = {"RED": ft.Colors.RED_500, "ORANGE": ft.Colors.ORANGE_500, "GREEN": ft.Colors.GREEN_600, "BLUE": ft.Colors.BLUE_600, "AMBER": ft.Colors.AMBER_600, "TEAL": ft.Colors.TEAL_600}
            advice_section = ft.Container(
                content=ft.Row([
                    ft.Icon(getattr(ft.Icons, adv.get("icon", "INFO"), ft.Icons.INFO), size=16, color="white"),
                    ft.Text(adv.get("text", ""), size=11, color="white", weight="w500", expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                ], alignment="center", spacing=8),
                bgcolor=color_map.get(adv.get("color"), ft.Colors.BLUE_GREY_500),
                padding=ft.padding.symmetric(vertical=8, horizontal=15), border_radius=12, margin=ft.margin.only(top=5)
            )

        return ft.Column([header, ft.Container(height=5), self.txt_timer, timeline_section, ft.Container(height=5), widgets_row, advice_section], spacing=0, tight=True)

    def _build_manual_ui(self, data):
        self.txt_marquee = ft.Text(self.config.get('manual_text', ''), size=40, weight="bold", color="white", no_wrap=True)
        self.marquee_view = ft.Container(content=ft.Stack([ft.Container(content=self.txt_marquee, left=0)]), height=60, clip_behavior=ft.ClipBehavior.HARD_EDGE, expand=True, alignment=ft.Alignment(0,0))
        return ft.Column([ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color="white30"), self._build_settings_btn()], alignment="spaceBetween"), ft.Container(height=20), self.marquee_view, ft.Container(height=20)])

    def _build_timer_ui(self, data):
        self.txt_timer = ft.Text("00:00:00", size=55, weight="bold", color=ft.Colors.CYAN_50, font_family="monospace")
        return ft.Column([ft.Row([ft.Container(), self._build_settings_btn()], alignment="spaceBetween"), ft.Container(expand=True, content=self.txt_timer, alignment=ft.Alignment(0,0))])

    def _update_realtime_values(self, data):
        if not hasattr(self, 'txt_timer') or not self.txt_timer.page: return
        try:
            cfg = data.get("config", {})
            start = datetime.strptime(cfg.get("start_date"), "%Y-%m-%d %H:%M:%S")
            target = datetime.strptime(cfg.get("target_date"), "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            
            ref = start if now < start else target
            diff = (ref - now).total_seconds()
            
            if diff <= 0:
                self.txt_timer.value = "CHEGAMOS! 🎉"
                self.txt_timer.color = ft.Colors.GREEN_300
                pct = 1.0 
            else:
                d, r = divmod(diff, 86400)
                h, r = divmod(r, 3600)
                m, s = divmod(r, 60)
                if d > 0: self.txt_timer.value = f"{int(d)}d {int(h):02}:{int(m):02}:{int(s):02}"
                else: self.txt_timer.value = f"{int(h):02}:{int(m):02}:{int(s):02}"
                self.txt_timer.color = "white"
                total = (target - start).total_seconds()
                pct = max(0.0, min(1.0, (now - start).total_seconds() / (total if total > 0 else 1)))

            self.txt_timer.update()

            if hasattr(self, 'progress_bar') and self.progress_bar.page:
                bar_w = pct * self.track_width
                self.progress_bar.width = bar_w
                icon_pos = bar_w - 7 
                if icon_pos < 0: icon_pos = 0
                if icon_pos > (self.track_width - 14): icon_pos = self.track_width - 14
                self.progress_icon.left = icon_pos
                self.progress_bar.parent.update()
        except: pass

    async def _animate_marquee(self):
        if not hasattr(self, 'marquee_view'): return
        try: w = getattr(self.page_ref, 'window_width', 400)
        except: w = 400
        self.marquee_offset = w
        while self.running and self.current_state == "MANUAL":
            try:
                self.marquee_offset -= 2
                if self.marquee_offset < -(len(self.txt_marquee.value)*20): self.marquee_offset = w
                if self.marquee_view.content:
                    self.marquee_view.content.controls[0].left = self.marquee_offset
                    self.marquee_view.update()
                await asyncio.sleep(0.016)
            except: break

    def _apply_theme(self):
        cfg = self.config
        if cfg.get("dynamic_theme", False):
            day = self.full_data.get("weather", {}).get("is_day", 1)
            colors = self.DYNAMIC_PALETTE["day"] if day else self.DYNAMIC_PALETTE["night"]
        else:
            colors = self.THEMES.get(cfg.get("theme", "Ocean"), self.THEMES["Ocean"])
        self.gradient = ft.LinearGradient(begin=ft.Alignment(-1,-1), end=ft.Alignment(1,1), colors=colors)

    def _glass_card(self, content, expand=False, on_click=None, ink=False, tooltip=None):
        return ft.Container(content=content, bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE), border_radius=12, padding=8, border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)), alignment=ft.Alignment(0,0), expand=expand, on_click=on_click, ink=ink, tooltip=tooltip)
    
    def _get_weather_icon(self, code, is_day):
        if code is None: code = 0
        if code == 0: return ft.Icons.WB_SUNNY if is_day else ft.Icons.NIGHTLIGHT_ROUND
        if code in [1,2,3]: return ft.Icons.WB_CLOUDY
        if code >= 50: return ft.Icons.WATER_DROP
        return ft.Icons.CLOUD

    def _build_settings_btn(self):
        return ft.IconButton(ft.Icons.SETTINGS, icon_color="white54", icon_size=18, on_click=self._open_admin, visible=self.is_admin)

    def _open_google_maps(self, e):
        loc = self.config.get("target_location", {})
        lat, lon = loc.get("lat"), loc.get("lon")
        if lat and lon: webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")
        else:
            name = loc.get("name", "Brasil")
            webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={name}")

    # --- POPUPS ---
    def _open_currency_converter(self, e):
        if self.weather_dialog in self.page_ref.overlay: self.page_ref.overlay.remove(self.weather_dialog)
        fin = self.full_data.get("finance", {})
        usd, blue, pyg = fin.get("usd", 5.0), fin.get("blue", 1000.0), fin.get("pyg", 1400.0)
        
        txt_brl = ft.TextField(label="Reais (BRL)", value="100", text_align="right", height=45, text_size=16, input_filter=ft.NumbersOnlyInputFilter(), border_color="cyan")
        lbl_usd = ft.Text(f"$ {(100/usd):.2f}", weight="bold", size=15, color="green")
        real_blue_rate = blue / usd if usd else 200
        lbl_blue = ft.Text(f"$ {(100 * real_blue_rate):.0f}", weight="bold", size=15, color="cyan")
        lbl_pyg = ft.Text(f"₲ {(100 * pyg):.0f}", weight="bold", size=15, color="orange")

        def calc(e):
            try: val = float(txt_brl.value)
            except: val = 0
            u = usd if usd > 0 else 1
            lbl_usd.value = f"$ {(val/u):.2f}"
            lbl_blue.value = f"$ {(val * real_blue_rate):.0f}"
            lbl_pyg.value = f"₲ {(val * pyg):.0f}"
            self.page_ref.update()
        txt_brl.on_change = calc

        content = ft.Column([ft.Text("Conversor Fronteira", size=12, color="white54", weight="bold"), ft.Container(height=10), txt_brl, ft.Divider(height=20, color="white10"), ft.Row([ft.Text("Dólar", width=60, color="white70"), lbl_usd], alignment="spaceBetween"), ft.Row([ft.Text("Peso Blue", width=70, color="white70"), lbl_blue], alignment="spaceBetween"), ft.Row([ft.Text("Guarani", width=60, color="white70"), lbl_pyg], alignment="spaceBetween"), ft.Container(height=10), ft.Text(f"Base: Blue {blue:.0f} | PYG {pyg:.0f}", size=9, color="white30", text_align="center")], tight=True)
        self.weather_dialog = ft.AlertDialog(content=ft.Container(content=content, width=260, height=340, padding=15), bgcolor=ft.Colors.GREY_900)
        self.page_ref.overlay.append(self.weather_dialog)
        self.weather_dialog.open = True
        self.page_ref.update()

    def _open_weather_details(self, e):
        if self.weather_dialog and self.weather_dialog in self.page_ref.overlay: self.page_ref.overlay.remove(self.weather_dialog)
        w = self.full_data.get("weather", {})
        def stat_row(icon, label, value, color): return ft.Container(content=ft.Row([ft.Container(content=ft.Icon(icon, color=color, size=20), bgcolor=ft.Colors.with_opacity(0.1, color), padding=8, border_radius=8), ft.Column([ft.Text(label, size=10, color="white54"), ft.Text(value, weight="bold", size=14)], spacing=2)], alignment="center"), bgcolor=ft.Colors.WHITE10, padding=10, border_radius=10, expand=True)
        forecast_items = []
        for day in w.get("forecast", []):
            try:
                dt = datetime.strptime(day['date'], "%Y-%m-%d")
                forecast_items.append(ft.Container(content=ft.Row([ft.Text(dt.strftime("%d/%m"), size=12, color="white70", width=50), ft.Icon(self._get_weather_icon(day['code'], 1), size=16, color="white"), ft.Row([ft.Text(f"{day['min']}°", size=12, color="cyan"), ft.Text(f"{day['max']}°", size=12, color="orange")], spacing=10)], alignment="spaceBetween"), padding=ft.padding.symmetric(vertical=5)))
            except: pass
        content = ft.Column([ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=12, color="white54"), ft.Text(self.config.get("target_location", {}).get("name"), size=12, color="white54")], alignment="center"), ft.Container(height=10), ft.Row([ft.Icon(self._get_weather_icon(w.get("code", 0), w.get("is_day", 1)), size=60, color="white"), ft.Column([ft.Text(f"{w.get('temp', '--')}°", size=48, weight="bold", height=48), ft.Text(w.get("desc", ""), size=14, color="white70")], spacing=0)], alignment="center"), ft.Container(height=20), ft.Row([stat_row(ft.Icons.THERMOSTAT, "Sensação", f"{w.get('feels_like', '--')}°", ft.Colors.ORANGE), stat_row(ft.Icons.WATER_DROP, "Umidade", f"{w.get('humidity', '--')}%", ft.Colors.BLUE)]), ft.Container(height=10), ft.Row([stat_row(ft.Icons.AIR, "Vento", f"{w.get('wind', '--')} km/h", ft.Colors.GREY)]), ft.Divider(color="white10", height=30), ft.Text("PRÓXIMOS DIAS", size=10, weight="bold", color="white30"), ft.Column(forecast_items, spacing=0)], tight=True)
        self.weather_dialog = ft.AlertDialog(content=ft.Container(content=content, width=300, height=450, padding=10), bgcolor=ft.Colors.GREY_900)
        self.page_ref.overlay.append(self.weather_dialog)
        self.weather_dialog.open = True
        self.page_ref.update()

    # --- ADMIN (FINAL) ---
    def _open_admin(self, e):
        if self.admin_dialog and self.admin_dialog in self.page_ref.overlay: self.page_ref.overlay.remove(self.admin_dialog)
        cfg = self.config
        
        self.dd_mode = ft.Dropdown(label="Modo", value=cfg.get("mode", "auto"), options=[ft.dropdown.Option("auto"), ft.dropdown.Option("manual"), ft.dropdown.Option("timer")], bgcolor=ft.Colors.BLACK26, border_radius=10, height=50)
        self.dd_theme = ft.Dropdown(label="Tema", value=cfg.get("theme", "Ocean"), options=[ft.dropdown.Option(k) for k in self.THEMES.keys()], bgcolor=ft.Colors.BLACK26, border_radius=10, height=50)
        self.sw_dynamic, ui_sw_dynamic = create_switch("Tema Dinâmico", cfg.get("dynamic_theme", True))

        self.tf_manual = create_input("Letreiro", ft.Icons.EDIT_NOTE, cfg.get("manual_text", ""))
        self.tf_advice = create_input("Dica Manual", ft.Icons.LIGHTBULB, cfg.get("manual_advice", ""))
        self.tf_start = create_input("Início", ft.Icons.DATE_RANGE, cfg.get("start_date", ""))
        self.tf_end = create_input("Fim", ft.Icons.FLAG, cfg.get("target_date", ""))
        self.tf_alert = create_input("Alerta Câmbio", ft.Icons.ATTACH_MONEY, str(cfg.get("alert_target", 5.20)))
        self.sw_alert, ui_sw_alert = create_switch("Ativar Alerta", cfg.get("alert_enabled", False))

        self.sw_tl, ui_sw_tl = create_switch("Timeline", cfg.get("show_timeline", True))
        self.sw_w, ui_sw_w = create_switch("Clima", cfg.get("show_weather", True))
        self.sw_c, ui_sw_c = create_switch("Moedas", cfg.get("show_currency", True))
        self.sw_a, ui_sw_a = create_switch("Dicas", cfg.get("show_advice", True))

        loc = cfg.get("target_location", {})
        self.tf_dest = create_input("Cidade", ft.Icons.LOCATION_CITY, loc.get("name", ""))
        self.tf_lat = create_input("Lat", ft.Icons.MAP, str(loc.get("lat", 0)))
        self.tf_lon = create_input("Lon", ft.Icons.MAP, str(loc.get("lon", 0)))
        
        self.txt_gps_status = ft.Text("Pronto.", size=11, color="white54", italic=True)
        self.prog_gps = ft.ProgressBar(width=100, color="cyan", bgcolor="transparent", visible=False)

        async def do_search(e):
            if not self.tf_dest.value: return
            self.txt_gps_status.value = "Buscando..."; self.prog_gps.visible = True; self.page_ref.update()
            res = await BannerService.search_location_api(self.tf_dest.value)
            self.prog_gps.visible = False
            if res:
                self.tf_dest.value = res["name"]
                self.tf_lat.value = str(res["lat"])
                self.tf_lon.value = str(res["lon"])
                self.txt_gps_status.value = f"✅ Encontrado: {res['label'][:25]}..."
            else:
                self.txt_gps_status.value = "❌ Local não encontrado."
            self.page_ref.update()
        
        def set_preset(e):
            presets = {"Foz do Iguaçu": (-25.51, -54.57), "Ciudad del Este": (-25.51, -54.61), "Puerto Iguazú": (-25.59, -54.57), "São Paulo": (-23.55, -46.63), "Rio de Janeiro": (-22.90, -43.17)}
            if e.control.value in presets:
                lat, lon = presets[e.control.value]
                self.tf_dest.value = e.control.value
                self.tf_lat.value = str(lat)
                self.tf_lon.value = str(lon)
                self.txt_gps_status.value = "✅ Preset carregado."
                self.page_ref.update()

        async def get_gps(e):
            if self.geolocator:
                self.txt_gps_status.value = "Aguardando satélites..."; self.prog_gps.visible = True; self.page_ref.update()
                try: await self.geolocator.handle_permission_request()
                except: 
                    self.txt_gps_status.value = "❌ Erro ao solicitar permissão."; self.prog_gps.visible = False; self.page_ref.update()
            else:
                self.txt_gps_status.value = "❌ GPS não disponível."; self.page_ref.update()

        btn_search = ft.IconButton(ft.Icons.SEARCH, on_click=do_search, bgcolor=ft.Colors.CYAN_700)
        btn_gps = ft.TextButton("Usar GPS", icon=ft.Icons.MY_LOCATION, on_click=get_gps)
        if not self.geolocator: btn_gps.disabled = True
        
        dd_presets = ft.Dropdown(label="Favoritos", options=[ft.dropdown.Option(k) for k in ["Foz do Iguaçu", "Ciudad del Este", "Puerto Iguazú", "São Paulo"]], bgcolor=ft.Colors.BLACK26, text_size=12, height=45)
        dd_presets.on_change = set_preset

        self.panels = {}
        self.panels["geral"] = ft.Column([ft.Text("Visual", color="white54", size=11, weight="bold"), self.dd_mode, self.dd_theme, ui_sw_dynamic], spacing=10, visible=True)
        self.panels["texto"] = ft.Column([ft.Text("Conteúdo", color="white54", size=11, weight="bold"), self.tf_manual, self.tf_advice, ft.Divider(), ft.Text("Datas", color="white54", size=11, weight="bold"), self.tf_start, self.tf_end], spacing=15, visible=False)
        self.panels["widgets"] = ft.Column([ft.Text("Elementos", color="white54", size=11, weight="bold"), ft.Container(content=ft.Column([ui_sw_tl, ui_sw_w, ui_sw_c, ui_sw_a], spacing=0), bgcolor=ft.Colors.BLACK26, border_radius=10, padding=10), ft.Divider(), ft.Text("Alerta Câmbio", color="white54", size=11, weight="bold"), self.tf_alert, ui_sw_alert], visible=False)
        self.panels["local"] = ft.Column([ft.Text("Localização", color="white54", size=11, weight="bold"), dd_presets, ft.Row([ft.Container(self.tf_dest, expand=True), btn_search]), ft.Row([ft.Container(self.tf_lat, expand=True), ft.Container(self.tf_lon, expand=True)], spacing=10), ft.Row([btn_gps, self.prog_gps, self.txt_gps_status], alignment="spaceBetween", vertical_alignment="center")], spacing=15, visible=False)

        try: w = getattr(self.page_ref, "window_width", 800) or 800
        except: w = 800
        is_mobile = w < 600
        dialog_width = w * 0.95 if is_mobile else 600

        self.content_area = ft.Container(content=ft.Column([p for p in self.panels.values()]), expand=True, padding=ft.padding.only(left=0 if is_mobile else 20, top=10 if is_mobile else 0))

        def switch_panel(e):
            target = e.control.data
            for k, p in self.panels.items(): p.visible = (k == target)
            btns = self.nav_mobile.controls if is_mobile else self.nav_desktop.controls
            for btn in btns:
                active = (btn.data == target)
                btn.icon_color = ft.Colors.CYAN_200 if active else ft.Colors.WHITE54
                if not is_mobile: btn.style = ft.ButtonStyle(color=ft.Colors.CYAN_200 if active else ft.Colors.WHITE54, bgcolor=ft.Colors.WHITE10 if active else ft.Colors.TRANSPARENT, alignment=ft.Alignment(-1,0))
            self.content_area.update()
            if is_mobile: self.nav_mobile.update()
            else: self.nav_desktop.update()

        self.nav_mobile = ft.Row([ft.IconButton(ft.Icons.SETTINGS, data="geral", on_click=switch_panel, icon_color=ft.Colors.CYAN_200), ft.IconButton(ft.Icons.DESCRIPTION, data="texto", on_click=switch_panel), ft.IconButton(ft.Icons.WIDGETS, data="widgets", on_click=switch_panel), ft.IconButton(ft.Icons.PLACE, data="local", on_click=switch_panel)], alignment="center")
        def nav_btn_desk(text, icon, key, active=False): return ft.TextButton(text, icon=icon, data=key, on_click=switch_panel, style=ft.ButtonStyle(color=ft.Colors.CYAN_200 if active else ft.Colors.WHITE54, bgcolor=ft.Colors.WHITE10 if active else ft.Colors.TRANSPARENT, alignment=ft.Alignment(-1, 0)), width=120, height=40)
        self.nav_desktop = ft.Column([nav_btn_desk("Geral", ft.Icons.SETTINGS, "geral", True), nav_btn_desk("Conteúdo", ft.Icons.DESCRIPTION, "texto"), nav_btn_desk("Widgets", ft.Icons.WIDGETS, "widgets"), nav_btn_desk("Local", ft.Icons.PLACE, "local")], spacing=5, width=130)

        if is_mobile: body = ft.Column([self.nav_mobile, ft.Divider(height=1), self.content_area], spacing=5)
        else: body = ft.Row([self.nav_desktop, ft.VerticalDivider(width=1), self.content_area], expand=True)

        self.admin_dialog = ft.AlertDialog(title=ft.Text("Configurações", size=18, weight="bold"), content=ft.Container(content=body, width=dialog_width, height=450), actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(self.admin_dialog, 'open', False) or self.page_ref.update()), ft.ElevatedButton("SALVAR", bgcolor=ft.Colors.CYAN_600, color="white", on_click=self._save_config)], actions_alignment="end", bgcolor=ft.Colors.GREY_900)
        self.page_ref.overlay.append(self.admin_dialog)
        self.admin_dialog.open = True
        self.page_ref.update()

    def _on_gps_position(self, e):
        if hasattr(self, 'tf_lat') and hasattr(self, 'tf_lon'):
            self.tf_lat.value = str(e.latitude)
            self.tf_lon.value = str(e.longitude)
            if hasattr(self, 'txt_gps_status'):
                self.prog_gps.visible = False
                self.txt_gps_status.value = "✅ Coordenadas OK!"
                self.page_ref.run_task(self._fetch_gps_name, e.latitude, e.longitude)
            self.page_ref.update()
    
    def _on_gps_error(self, e):
        if hasattr(self, 'txt_gps_status'):
            self.prog_gps.visible = False
            self.txt_gps_status.value = "❌ Erro ao obter GPS."
            self.page_ref.update()

    async def _fetch_gps_name(self, lat, lon):
        name = await BannerService.get_location_name(lat, lon)
        if hasattr(self, 'tf_dest'):
            self.tf_dest.value = name
            if hasattr(self, 'txt_gps_status'): self.txt_gps_status.value = f"✅ Local: {name}"
            self.page_ref.update()

    async def _save_config(self, e):
        try:
            new = {
                "mode": self.dd_mode.value, "theme": self.dd_theme.value, "dynamic_theme": self.sw_dynamic.value,
                "manual_text": self.tf_manual.value, "manual_advice": self.tf_advice.value,
                "start_date": self.tf_start.value, "target_date": self.tf_end.value,
                "show_timeline": self.sw_tl.value, "show_weather": self.sw_w.value, "show_currency": self.sw_c.value, "show_advice": self.sw_a.value,
                "alert_enabled": self.sw_alert.value, "alert_target": float(self.tf_alert.value or 0),
                "target_location": {"name": self.tf_dest.value, "lat": float(self.tf_lat.value), "lon": float(self.tf_lon.value)}
            }
            await BannerService.save_config(new)
            self.admin_dialog.open = False
            self.force_refresh = True
            self.page_ref.update()
            snack = ft.SnackBar(ft.Text("Salvo!"), bgcolor=ft.Colors.GREEN_700)
            self.page_ref.overlay.append(snack)
            snack.open = True
            self.page_ref.update()
        except Exception as ex:
            print(f"Erro salvar: {ex}")

def create_input(label, icon, value=""):
    return ft.TextField(label=label, value=value, prefix_icon=icon, text_size=13, bgcolor=ft.Colors.BLACK26, border_color=ft.Colors.WHITE10, focused_border_color=ft.Colors.CYAN_400, border_radius=10, height=45, content_padding=10)

def create_switch(label, value):
    sw = ft.Switch(value=value, active_color=ft.Colors.CYAN_400)
    return sw, ft.Container(content=ft.Row([ft.Text(label, size=13, weight="w500"), sw], alignment="spaceBetween"), padding=ft.padding.symmetric(vertical=5, horizontal=5))