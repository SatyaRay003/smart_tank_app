import flet as ft
from auth_service import AuthService
from firestore_service import FirestoreService
from state import session

def AuthView(page: ft.Page):
    email_field = ft.TextField(label="Email", width=320, keyboard_type=ft.KeyboardType.EMAIL)
    password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=320)
    status_text = ft.Text(color=ft.Colors.RED_ACCENT, text_align=ft.TextAlign.CENTER)
    progress_ring = ft.ProgressRing(visible=False, width=24, height=24)
    
    # Clickable text button for password reset
    forgot_password_btn = ft.TextButton(
        content=ft.Text("Forgot Password?", color=ft.Colors.BLUE_600),
        visible=False,
    )

    error_container = ft.Column(
        controls=[
            status_text,
            forgot_password_btn,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
    )

    def handle_forgot_password(e):
        email = email_field.value.strip() if email_field.value else ""
        if not email:
            status_text.value = "Please enter your email to reset password."
            status_text.color = ft.Colors.RED_ACCENT
            forgot_password_btn.visible = False
            page.update()
            return

        try:
            progress_ring.visible = True
            page.update()
            AuthService.send_password_reset_email(email)
            status_text.value = "Password reset link sent to your email."
            status_text.color = ft.Colors.GREEN_ACCENT
            forgot_password_btn.visible = False
        except Exception as err:
            status_text.value = str(err)
            status_text.color = ft.Colors.RED_ACCENT
        finally:
            progress_ring.visible = False
            page.update()

    forgot_password_btn.on_click = handle_forgot_password

    def route_after_auth(user_id, id_token):
        FirestoreService.update_email_verification_status(user_id, True, id_token)
        device_id = FirestoreService.get_user_device_id(user_id, id_token)
        
        session["user_id"] = user_id
        session["id_token"] = id_token
        session["device_id"] = device_id
        
        # Always route to register-device to allow continuing with existing or adding new
        page.go("/register-device")

    def handle_sign_in(e):
        email = email_field.value.strip() if email_field.value else ""
        password = password_field.value.strip() if password_field.value else ""

        forgot_password_btn.visible = False

        if not email or not password:
            status_text.value = "Please enter both email and password."
            status_text.color = ft.Colors.RED_ACCENT
            page.update()
            return

        try:
            status_text.value = ""
            progress_ring.visible = True
            page.update()
            
            res = AuthService.sign_in(email, password)
            route_after_auth(res["localId"], res["idToken"])
        except Exception as err:
            err_msg = str(err)
            
            if "verify your account" in err_msg.lower():
                status_text.value = "Please verify your account using the link sent to your email."
                status_text.color = ft.Colors.ORANGE_ACCENT
                forgot_password_btn.visible = False
            elif "wrong password" in err_msg.lower():
                status_text.value = "Wrong password."
                status_text.color = ft.Colors.RED_ACCENT
                forgot_password_btn.visible = True
            elif "user does not exist" in err_msg.lower():
                status_text.value = "User does not exist. Sign up please."
                status_text.color = ft.Colors.RED_ACCENT
                forgot_password_btn.visible = False
            else:
                status_text.value = err_msg
                status_text.color = ft.Colors.RED_ACCENT
                forgot_password_btn.visible = False
        finally:
            progress_ring.visible = False
            page.update()

    def handle_sign_up(e):
        email = email_field.value.strip() if email_field.value else ""
        password = password_field.value.strip() if password_field.value else ""

        forgot_password_btn.visible = False

        if not email or not password:
            status_text.value = "Please enter both email and password."
            status_text.color = ft.Colors.RED_ACCENT
            page.update()
            return

        if len(password) < 6:
            status_text.value = "Password must be at least 6 characters."
            status_text.color = ft.Colors.RED_ACCENT
            page.update()
            return

        try:
            status_text.value = ""
            progress_ring.visible = True
            page.update()
            
            res = AuthService.sign_up(email, password)
            FirestoreService.create_user_profile(res["localId"], email, False, res["idToken"])
            status_text.value = "Verification link sent! Check your email before logging in."
            status_text.color = ft.Colors.GREEN_ACCENT
        except Exception as err:
            status_text.value = str(err)
            status_text.color = ft.Colors.RED_ACCENT
        finally:
            progress_ring.visible = False
            page.update()

    return ft.View(
        route="/",
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.WATER_DROP, size=60, color=ft.Colors.BLUE),
                        ft.Text("Smart Tank Controller", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Sign in or create an account", size=14, color=ft.Colors.GREY_600),
                        email_field,
                        password_field,
                        ft.Row(
                            [
                                ft.ElevatedButton("Login", on_click=handle_sign_in, width=120),
                                ft.OutlinedButton("Sign Up", on_click=handle_sign_up, width=120),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        progress_ring,
                        error_container,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=20,
            )
        ],
    )