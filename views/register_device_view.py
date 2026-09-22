import flet as ft
from firestore_service import FirestoreService
from state import session

def RegisterDeviceView(page: ft.Page):
    user_id = session.get("user_id")
    id_token = session.get("id_token")
    current_device_id = session.get("device_id")

    device_id_field = ft.TextField(
        label="Enter Device ID",
        hint_text="e.g. DEV_12345",
        width=320
    )
    error_text = ft.Text(color=ft.Colors.RED_ACCENT, text_align=ft.TextAlign.CENTER)

    def handle_use_existing(e):
        page.go("/dashboard")

    def handle_add_or_replace_device(e):
        new_dev_id = device_id_field.value.strip() if device_id_field.value else ""
        
        if not new_dev_id:
            error_text.value = "Device ID cannot be empty."
            page.update()
            return

        # If user typed the exact same device ID already active
        if current_device_id and new_dev_id == current_device_id:
            page.go("/dashboard")
            return

        try:
            # 1. Check if new device exists in Firestore
            if not FirestoreService.device_exists(new_dev_id, id_token):
                error_text.value = "Device does not exist. Please register the device."
                page.update()
                return

            # 2. Check if the device is already claimed by another user
            owner = FirestoreService.get_device_owner(new_dev_id, id_token)
            if owner and owner != user_id:
                error_text.value = "Device already registered with other user"
                page.update()
                return

            # 3. Re-link: Nullifies old damaged device ownerId and registers new one
            FirestoreService.link_device_to_user(
                user_id=user_id,
                new_device_id=new_dev_id,
                id_token=id_token,
                old_device_id=current_device_id
            )

            # Update session state and proceed
            session["device_id"] = new_dev_id
            page.go("/dashboard")
        except Exception as err:
            error_text.value = f"Failed to link device: {str(err)}"
            page.update()

    # Build dynamic UI controls
    controls_list = [
        ft.Icon(ft.Icons.ROUTER, size=48, color=ft.Colors.BLUE),
        ft.Text("Device Setup", size=22, weight=ft.FontWeight.BOLD),
    ]

    # Show "Use existing" button if a registered device is already on the account
    if current_device_id:
        controls_list.extend([
            ft.Text(f"Current Device: {current_device_id}", size=14, color=ft.Colors.GREY_700),
            ft.ElevatedButton(
                f"Use existing registered Device {current_device_id}",
                on_click=handle_use_existing,
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                width=320,
            ),
            ft.Divider(height=20, thickness=1),
            ft.Text("Or replace with a new device:", size=13, color=ft.Colors.GREY_600),
        ])
    else:
        controls_list.append(
            ft.Text("No device linked to this account. Enter your Device ID:", text_align=ft.TextAlign.CENTER)
        )

    controls_list.extend([
        device_id_field,
        ft.OutlinedButton(
            "Add New Device" if current_device_id else "Add Device",
            on_click=handle_add_or_replace_device,
            width=220,
        ),
        error_text,
    ])

    return ft.View(
        route="/register-device",
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=controls_list,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                padding=20,
            )
        ],
    )