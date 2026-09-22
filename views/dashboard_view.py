import flet as ft
from datetime import datetime, timezone, timedelta
from firestore_service import FirestoreService
from state import session

# Indian Standard Time (IST) offset: UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))

def format_datetime_ist(timestamp_str, prefix=""):
    if not timestamp_str or timestamp_str == "N/A":
        return f"{prefix}Not recorded yet" if prefix else "Not recorded yet"
    
    try:
        clean_ts = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        # If naive, assume it was recorded in UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_ist = dt.astimezone(IST)
    except Exception:
        return f"{prefix}{timestamp_str}"
        
    hour_minute = dt_ist.strftime("%I:%M %p").lstrip("0")
    day = dt_ist.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        
    date_part = f"{day}{suffix} {dt_ist.strftime('%b %Y')}"
    return f"{prefix}{hour_minute}, {date_part}"

def DashboardView(page: ft.Page):
    device_id = session.get("device_id")
    id_token = session.get("id_token")
    
    level_bar = ft.ProgressBar(width=300, value=0.0, color=ft.Colors.BLUE, bgcolor=ft.Colors.GREY_300)
    
    # Replaces 'High' label with the prominent, bold Last High text
    last_high_text = ft.Text(
        "Checking...",
        size=22,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_900,
        text_align=ft.TextAlign.CENTER,
    )
    
    pump_switch = ft.Switch(
        label="Pump Status: OFF",
        value=False,
        active_color="#66de90",
        inactive_thumb_color="#e89a7d",
        inactive_track_color="#fce8e3"
    )
    
    last_pump_text = ft.Text(
        "Connecting...",
        size=12,
        color=ft.Colors.GREY_600,
        text_align=ft.TextAlign.CENTER,
    )

    def on_pump_toggle(e):
        new_status = "ON" if pump_switch.value else "OFF"
        pump_switch.label = f"Pump Status: {new_status}"
        FirestoreService.update_pump_status(device_id, new_status, id_token)
        page.update()

    pump_switch.on_change = on_pump_toggle

    def on_device_data(data):
        water_level_sensor = data.get("waterLevel", "EMPTY").upper()
        pump_status = data.get("pumpStatus", "OFF").upper()
        last_pump_time = data.get("lastPumpTimestamp", "N/A")
        last_full_time = data.get("lastFullTimestamp", None)

        # Update progress bar
        if water_level_sensor in ["HIGH", "S1"]:
            level_bar.value = 1.0
        elif water_level_sensor in ["MEDIUM", "S2"]:
            level_bar.value = 0.66
        elif water_level_sensor in ["LOW", "S3"]:
            level_bar.value = 0.33
        else:
            level_bar.value = 0.0

        # Update main Last High text
        if last_full_time:
            last_high_text.value = format_datetime_ist(last_full_time, prefix="Last High at ")
        elif water_level_sensor in ["HIGH", "S1"] and last_pump_time != "N/A":
            last_high_text.value = format_datetime_ist(last_pump_time, prefix="Last High at ")
        else:
            last_high_text.value = "Last High: Not recorded yet"

        # Update pump toggle and footer
        is_pump_on = (pump_status == "ON")
        pump_switch.value = is_pump_on
        pump_switch.label = f"Pump Status: {pump_status}"
        
        last_pump_text.value = format_datetime_ist(
            last_pump_time, 
            prefix="Last Pump Status Updated at "
        )
        
        page.update()

    watcher = FirestoreService.listen_to_device(device_id, id_token, on_device_data)
    session["device_watcher"] = watcher

    def handle_logout(e):
        if "device_watcher" in session and session["device_watcher"]:
            session["device_watcher"].unsubscribe()
        session.clear()
        page.go("/")

    return ft.View(
        route="/dashboard",
        controls=[
            ft.AppBar(
                title=ft.Text(f"Tank Monitor ({device_id})"),
                actions=[ft.IconButton(ft.Icons.LOGOUT, on_click=handle_logout, tooltip="Log Out")],
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Icon(ft.Icons.WATER_DROP, size=50, color=ft.Colors.BLUE_ACCENT),
                                        ft.Text("Live Water Level", size=16, weight=ft.FontWeight.W_500),
                                        last_high_text,
                                        level_bar,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=12,
                                ),
                                padding=24,
                                width=340,
                            )
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text("Pump Switch", size=16, weight=ft.FontWeight.W_500),
                                        pump_switch,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10,
                                ),
                                padding=20,
                                width=340,
                            )
                        ),
                        last_pump_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=20,
            ),
        ],
    )