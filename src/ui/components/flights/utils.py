import flet as ft
from datetime import datetime, timedelta

def parse_dt(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
    except:
        return None

def calculate_trip_stats(segments):
    if not segments: return None

    first_seg = segments[0]
    last_seg = segments[-1]

    start_dt = parse_dt(first_seg.get("date"), first_seg.get("time"))
    last_dep_dt = parse_dt(last_seg.get("date"), last_seg.get("time"))
    last_arr_str = last_seg.get("arr_time", last_seg.get("time"))
    
    if last_dep_dt:
        end_dt = datetime.strptime(f"{last_seg.get('date')} {last_arr_str}", "%d/%m/%Y %H:%M")
        if end_dt < last_dep_dt:
            end_dt += timedelta(days=1)
    else:
        end_dt = None

    status = "future"
    progress = 0.0
    now = datetime.now()
    status_text = "Em breve"
    status_color = ft.Colors.GREY

    if start_dt and end_dt:
        total_duration = end_dt - start_dt
        
        if now < start_dt:
            diff = start_dt - now
            if diff.days == 0:
                status_text = f"Embarque em {diff.seconds // 3600}h"
                status_color = ft.Colors.ORANGE
            else:
                status_text = f"Faltam {diff.days} dias"
                status_color = ft.Colors.BLUE
        elif now > end_dt:
            status = "done"
            status_text = "Viagem Concluída"
            status_color = ft.Colors.GREEN
            progress = 1.0
        else:
            elapsed = now - start_dt
            progress = min(elapsed.total_seconds() / total_duration.total_seconds(), 1.0)
            
            is_flying = False
            current_seg_code = ""
            
            for seg in segments:
                s_dep = parse_dt(seg.get("date"), seg.get("time"))
                s_arr_str = seg.get("arr_time", seg.get("time"))
                if s_dep:
                    s_arr = datetime.strptime(f"{seg.get('date')} {s_arr_str}", "%d/%m/%Y %H:%M")
                    if s_arr < s_dep: s_arr += timedelta(days=1)
                    
                    if s_dep <= now <= s_arr:
                        is_flying = True
                        current_seg_code = seg.get("code")
                        break
            
            if is_flying:
                status = "flying"
                status_text = f"EM VOO: {current_seg_code}"
                status_color = ft.Colors.RED_400
            else:
                status = "connection"
                status_text = "EM CONEXÃO"
                status_color = ft.Colors.AMBER

        hours, remainder = divmod(total_duration.seconds, 3600)
        mins = remainder // 60
        days = total_duration.days
        duration_str = f"{hours}h {mins}m"
        if days > 0: duration_str = f"{days}d {duration_str}"

        return {
            "status": status,
            "status_text": status_text,
            "status_color": status_color,
            "progress": progress,
            "duration_str": duration_str
        }
    return None