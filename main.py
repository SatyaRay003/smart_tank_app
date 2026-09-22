import flet as ft
from views.auth_view import AuthView
from views.register_device_view import RegisterDeviceView
from views.dashboard_view import DashboardView

def main(page: ft.Page):
    page.title = "Smart Water Tank"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 390
    page.window_height = 700

    def route_change(e):
        page.views.clear()
        if page.route == "/":
            page.views.append(AuthView(page))
        elif page.route == "/register-device":
            page.views.append(RegisterDeviceView(page))
        elif page.route == "/dashboard":
            page.views.append(DashboardView(page))
        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Initialize the first view directly
    page.views.append(AuthView(page))
    page.update()

if __name__ == "__main__":
    ft.run(main)