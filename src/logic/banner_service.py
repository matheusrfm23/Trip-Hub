import json
import os
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
from src.core.config import ASSETS_DIR
from src.core.locker import file_lock
from src.core.logger import get_logger

log = get_logger("BannerService")

class BannerService:
    CONFIG_FILE = os.path.join(ASSETS_DIR, "data", "banner_config.json")
    SCHEDULE_FILE = os.path.join(ASSETS_DIR, "data", "schedule.json")
    
    # SUA CHAVE EXATA (Sem decodificar)
    ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImEwNjFjNmNhZmJiNTQ5OTI5Y2UwNmU2MzdjOTY2MGFjIiwiaCI6Im11cm11cjY0In0="

    _mem_cache = {
        "finance": {"ts": 0, "data": {"usd": 5.0, "eur": 6.0, "ars": 0.005, "blue": 1000.0, "pyg": 1400.0}},
        "weather": {
            "ts": 0, 
            "data": {
                "temp": 25, "code": 0, "desc": "Padrão", "is_day": 1,
                "feels_like": 25, "humidity": 50, "wind": 10,
                "rain_prob": 0,
                "forecast": [] 
            }
        }
    }

    @classmethod
    def get_config(cls):
        default = {
            "mode": "auto", "theme": "Ocean", "dynamic_theme": True,
            "manual_text": "TripHub System", "manual_advice": "",
            "start_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_date": "2026-12-31 00:00:00",
            "target_location": {"lat": -25.51, "lon": -54.57, "name": "Foz do Iguaçu"},
            "show_timeline": True, "show_weather": True, "show_currency": True, "show_advice": True,
            "alert_enabled": False, "alert_target": 5.20
        }
        if not os.path.exists(cls.CONFIG_FILE): return default
        try:
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for k, v in default.items():
                    if k not in saved: saved[k] = v
                return saved
        except: return default

    @classmethod
    async def save_config(cls, new_config):
        current = cls.get_config()
        current.update(new_config)
        try:
            with file_lock():
                with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=4)
            cls._mem_cache["weather"]["ts"] = 0 
        except Exception as e:
            log.error(f"Erro ao salvar config: {e}")

    @classmethod
    async def get_oracle_data(cls, user_id=None):
        try:
            config = cls.get_config()
            now = datetime.now()

            tasks = []
            if time.time() - cls._mem_cache["finance"]["ts"] > 300:
                tasks.append(cls._fetch_finance_realtime())
            
            if time.time() - cls._mem_cache["weather"]["ts"] > 1200:
                tasks.append(cls._fetch_weather_realtime(config))

            tasks.append(cls._check_schedule())

            try:
                results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=3.0)
                active_event = results[-1] if (results and not isinstance(results[-1], Exception)) else None
            except asyncio.TimeoutError:
                active_event = None

            state = "PLANNING"
            mode = config.get("mode", "auto")
            
            if mode == "manual": state = "MANUAL"
            elif mode == "timer": state = "TIMER"
            elif active_event:
                state = "MANUAL"
                config["manual_text"] = f"📅 AGORA: {active_event.get('title', 'Evento')}"
            elif cls._is_traveling(config, now):
                state = "TRAVELING"

            weather_data = cls._mem_cache["weather"]["data"]
            finance_data = cls._mem_cache["finance"]["data"]
            
            alert_active = False
            if config.get("alert_enabled"):
                if finance_data["usd"] <= float(config.get("alert_target", 0)):
                    alert_active = True

            advice = cls._generate_smart_advice(state, weather_data, config, alert_active)

            return {
                "state": state, "config": config, "weather": weather_data,
                "finance": finance_data, "flight": {"is_flight": False}, 
                "advice": advice, "alert_active": alert_active
            }
        except Exception as e:
            print(f"CRITICAL BANNER ERROR: {e}")
            return {
                "state": "PLANNING", "config": cls.get_config(),
                "weather": cls._mem_cache["weather"]["data"],
                "finance": cls._mem_cache["finance"]["data"],
                "flight": {"is_flight": False},
                "advice": {"text": "Sistema online.", "icon": "CHECK", "color": "BLUE"},
                "alert_active": False
            }

    # --- GEOLOCALIZAÇÃO HÍBRIDA (ORS + OPENMETEO) ---
    @classmethod
    async def search_location_api(cls, query):
        """Tenta ORS, se falhar, usa OpenMeteo (Gratuito)"""
        
        # 1. TENTATIVA OPENROUTESERVICE
        url_ors = "https://api.openrouteservice.org/geocode/search"
        params_ors = {"api_key": cls.ORS_API_KEY, "text": query, "size": 1}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url_ors, params=params_ors, timeout=3) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        features = data.get("features", [])
                        if features:
                            props = features[0].get("properties", {})
                            geom = features[0].get("geometry", {}).get("coordinates", [])
                            if len(geom) >= 2:
                                print(f"📍 Local encontrado via ORS: {props.get('label')}")
                                return {"name": props.get("name", query), "label": props.get("label", query), "lon": geom[0], "lat": geom[1]}
                    else:
                        print(f"⚠️ Erro ORS ({resp.status}): Tentando Fallback...")
        except Exception as e:
            print(f"⚠️ Exceção ORS: {e}")

        # 2. PLANO B: OPEN-METEO GEOCODING (Sem Key)
        print("🔄 Tentando OpenMeteo Geocoding...")
        url_om = "https://geocoding-api.open-meteo.com/v1/search"
        params_om = {"name": query, "count": 1, "language": "pt", "format": "json"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url_om, params=params_om, timeout=3) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", [])
                        if results:
                            item = results[0]
                            full_name = f"{item.get('name')}, {item.get('country_code')}"
                            print(f"📍 Local encontrado via OpenMeteo: {full_name}")
                            return {"name": item.get("name"), "label": full_name, "lat": item.get("latitude"), "lon": item.get("longitude")}
        except Exception as e:
            print(f"❌ Erro OpenMeteo: {e}")
            
        return None

    @classmethod
    async def get_location_name(cls, lat, lon):
        """Tenta descobrir o nome da cidade pelas coordenadas"""
        # Fallback direto para OpenMeteo Reverso (Mais simples)
        url = "https://geocoding-api.open-meteo.com/v1/reverse"
        # ?latitude=52.52&longitude=13.41&language=pt&format=json
        try:
            async with aiohttp.ClientSession() as session:
                # Url precisa ser montada ou usar params corretos da lib nova do openmeteo, 
                # mas o endpoint direto é esse. Note que nem sempre está habilitado no plano free básico sem lat/lon exatos.
                # Vamos tentar Nominatim (OpenStreetMap) que é o padrão da comunidade
                url_osm = "https://nominatim.openstreetmap.org/reverse"
                params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10}
                headers = {"User-Agent": "TripHub/1.0"}
                
                async with session.get(url_osm, params=params, headers=headers, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        addr = data.get("address", {})
                        return addr.get("city") or addr.get("town") or addr.get("municipality") or "Local GPS"
        except: pass
        return f"GPS ({lat:.3f}, {lon:.3f})"

    # --- APIS FINANCEIRAS/CLIMA ---
    @classmethod
    async def _fetch_finance_realtime(cls):
        url_awesome = "https://economia.awesomeapi.com.br/last/USD-BRL,BRL-PYG"
        url_blue = "https://api.bluelytics.com.ar/v2/latest"
        try:
            async with aiohttp.ClientSession() as session:
                res_aw, res_bl = await asyncio.gather(
                    session.get(url_awesome, timeout=2),
                    session.get(url_blue, timeout=2),
                    return_exceptions=True
                )
                usd = cls._mem_cache["finance"]["data"]["usd"]
                pyg = cls._mem_cache["finance"]["data"]["pyg"]
                blue = cls._mem_cache["finance"]["data"]["blue"]

                if not isinstance(res_aw, Exception) and res_aw.status == 200:
                    data = await res_aw.json()
                    usd = float(data.get("USDBRL", {}).get("bid", usd))
                    pyg = float(data.get("BRLPYG", {}).get("bid", pyg))

                if not isinstance(res_bl, Exception) and res_bl.status == 200:
                    data = await res_bl.json()
                    blue = float(data.get("blue", {}).get("value_sell", blue))

                cls._mem_cache["finance"] = {
                    "ts": time.time(),
                    "data": {"usd": usd, "blue": blue, "pyg": pyg}
                }
        except: pass

    @classmethod
    async def _fetch_weather_realtime(cls, config):
        loc = config.get("target_location", {})
        lat = loc.get("lat", -25.51)
        lon = loc.get("lon", -54.57)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=3) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        curr = data.get("current", {})
                        code = curr.get("weather_code", 0)
                        daily = data.get("daily", {})
                        
                        rain_prob = 0
                        if daily and "precipitation_probability_max" in daily:
                            try: rain_prob = daily["precipitation_probability_max"][0]
                            except: pass

                        forecast_list = []
                        if daily:
                            for i in range(3):
                                try:
                                    forecast_list.append({
                                        "date": daily["time"][i],
                                        "max": daily["temperature_2m_max"][i],
                                        "min": daily["temperature_2m_min"][i],
                                        "code": daily["weather_code"][i]
                                    })
                                except: pass

                        cls._mem_cache["weather"] = {
                            "ts": time.time(),
                            "data": {
                                "temp": curr.get("temperature_2m", 0),
                                "code": code,
                                "is_day": curr.get("is_day", 1),
                                "desc": cls._get_weather_desc(code),
                                "feels_like": curr.get("apparent_temperature", 0),
                                "humidity": curr.get("relative_humidity_2m", 0),
                                "wind": curr.get("wind_speed_10m", 0),
                                "rain_prob": rain_prob,
                                "forecast": forecast_list
                            }
                        }
        except: pass

    @classmethod
    async def _check_schedule(cls):
        if not os.path.exists(cls.SCHEDULE_FILE): return None
        try:
            with open(cls.SCHEDULE_FILE, 'r') as f: schedule = json.load(f)
            now = datetime.now()
            for event in schedule:
                start = datetime.strptime(event["start"], "%Y-%m-%d %H:%M")
                end = datetime.strptime(event["end"], "%Y-%m-%d %H:%M")
                if start <= now <= end: return event
        except: pass
        return None

    @staticmethod
    def _is_traveling(config, now):
        try:
            start = datetime.strptime(config.get("start_date"), "%Y-%m-%d %H:%M:%S")
            target = datetime.strptime(config.get("target_date"), "%Y-%m-%d %H:%M:%S")
            return start <= now <= (target + timedelta(days=1))
        except: return False

    @staticmethod
    def _get_weather_desc(code):
        try: code = int(code)
        except: code = 0
        if code == 0: return "Céu Limpo"
        if code in [1, 2, 3]: return "Nublado"
        if code in [45, 48]: return "Neblina"
        if 51 <= code <= 67: return "Chuva Leve"
        if code >= 80: return "Tempestade"
        return "Normal"

    @staticmethod
    def _generate_smart_advice(state, weather, config, alert_active):
        if alert_active:
            target = config.get("alert_target", 0)
            return {"text": f"Dólar abaixo de R$ {target:.2f}! Compre agora.", "icon": "ATTACH_MONEY", "color": "GREEN"}

        manual = config.get("manual_advice", "").strip()
        if manual:
            return {"text": manual, "icon": "EDIT", "color": "TEAL"}

        hour = datetime.now().hour
        greet = "Bom dia" if 5 <= hour < 12 else "Boa tarde" if 12 <= hour < 18 else "Boa noite"

        try: temp = float(weather.get("temp") or 0)
        except: temp = 25.0
        try: code = int(weather.get("code") or 0)
        except: code = 0
        
        if code >= 80: return {"text": f"{greet}. Tempestade! Fique seguro.", "icon": "THUNDERSTORM", "color": "BLUE_GREY"}
        if 51 <= code <= 67: return {"text": f"{greet}. Leve guarda-chuva.", "icon": "UMBRELLA", "color": "BLUE"}
        if temp >= 32: return {"text": f"{greet}. Calor intenso!", "icon": "WATER_DROP", "color": "ORANGE"}
        
        if state == "TRAVELING": return {"text": f"{greet}. Aproveite a viagem!", "icon": "CAMERA_ALT", "color": "GREEN"}
        
        return {"text": f"{greet}. Tudo pronto?", "icon": "EDIT_NOTE", "color": "PURPLE"}

    @classmethod
    async def get_smart_info(cls, user_id=None):
        return await cls.get_oracle_data(user_id)