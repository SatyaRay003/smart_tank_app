import requests
import threading
import time
from datetime import datetime
from firebase_config import FIRESTORE_REST_URL, FIREBASE_WEB_API_KEY

class FirestoreService:
    @staticmethod
    def _headers(id_token=None):
        headers = {"Content-Type": "application/json"}
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"
        return headers

    @staticmethod
    def email_exists(email):
        """Checks if a user with the given email exists in the Firestore 'users' collection."""
        url = f"{FIRESTORE_REST_URL}:runQuery?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "structuredQuery": {
                "from": [{"collectionId": "users"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "email"},
                        "op": "EQUAL",
                        "value": {"stringValue": str(email).strip().lower()}
                    }
                },
                "limit": 1
            }
        }
        try:
            res = requests.post(url, json=payload).json()
            if isinstance(res, list):
                for item in res:
                    if "document" in item:
                        return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_user_device_id(user_id, id_token):
        url = f"{FIRESTORE_REST_URL}/users/{user_id}"
        res = requests.get(url, headers=FirestoreService._headers(id_token)).json()
        if "fields" in res and "deviceId" in res["fields"]:
            return res["fields"]["deviceId"].get("stringValue")
        return None

    @staticmethod
    def create_user_profile(user_id, email, is_verified, id_token):
        url = f"{FIRESTORE_REST_URL}/users/{user_id}"
        body = {
            "fields": {
                "email": {"stringValue": str(email).strip().lower()},
                "isEmailVerified": {"booleanValue": bool(is_verified)},
                "deviceId": {"nullValue": None},
                "createdAt": {"stringValue": datetime.utcnow().isoformat()}
            }
        }
        response = requests.patch(url, json=body, headers=FirestoreService._headers(id_token))
        if response.status_code >= 400:
            print(f"[Firestore Error] Failed to create user profile: {response.text}")

    @staticmethod
    def update_email_verification_status(user_id, is_verified, id_token):
        url = f"{FIRESTORE_REST_URL}/users/{user_id}?updateMask.fieldPaths=isEmailVerified"
        body = {
            "fields": {
                "isEmailVerified": {"booleanValue": bool(is_verified)}
            }
        }
        requests.patch(url, json=body, headers=FirestoreService._headers(id_token))

    @staticmethod
    def device_exists(device_id, id_token):
        url = f"{FIRESTORE_REST_URL}/devices/{device_id}"
        response = requests.get(url, headers=FirestoreService._headers(id_token))
        if response.status_code == 200:
            res = response.json()
            return "fields" in res
        return False

    @staticmethod
    def get_device_owner(device_id, id_token):
        """Retrieves the ownerId associated with the device if it exists."""
        url = f"{FIRESTORE_REST_URL}/devices/{device_id}"
        response = requests.get(url, headers=FirestoreService._headers(id_token))
        if response.status_code == 200:
            res = response.json()
            if "fields" in res and "ownerId" in res["fields"]:
                return res["fields"]["ownerId"].get("stringValue")
        return None

    @staticmethod
    def archive_and_delete_device(device_id, user_id, id_token):
        """Copies device data to 'archived_devices' and deletes it from 'devices'."""
        device_url = f"{FIRESTORE_REST_URL}/devices/{device_id}"
        get_res = requests.get(device_url, headers=FirestoreService._headers(id_token))
        
        if get_res.status_code != 200:
            print(f"[Archive Error] Device {device_id} not found: {get_res.text}")
            return

        doc_data = get_res.json()
        archived_fields = doc_data.get("fields", {})
        
        # Inject archive metadata
        archived_fields["archivedAt"] = {"stringValue": datetime.utcnow().isoformat()}
        archived_fields["lastOwnerId"] = {"stringValue": str(user_id)}
        
        # Write to archived_devices
        archive_url = f"{FIRESTORE_REST_URL}/archived_devices/{device_id}"
        post_res = requests.patch(
            archive_url,
            json={"fields": archived_fields},
            headers=FirestoreService._headers(id_token)
        )
        
        if post_res.status_code not in [200, 201]:
            print(f"[Archive Error] Failed to write to archived_devices: {post_res.text}")
            raise Exception(f"Failed to archive damaged device: {post_res.text}")

        # Delete original document only after successful archiving
        del_res = requests.delete(device_url, headers=FirestoreService._headers(id_token))
        if del_res.status_code not in [200, 204]:
            print(f"[Archive Error] Failed to delete original device: {del_res.text}")

    @staticmethod
    def link_device_to_user(user_id, new_device_id, id_token, old_device_id=None):
        """
        Archives/deletes the old damaged device and registers the new device to the user.
        """
        # 1. Archive and delete damaged device if replacing
        if old_device_id and old_device_id != new_device_id:
            FirestoreService.archive_and_delete_device(old_device_id, user_id, id_token)

        # 2. Update user's profile with the new deviceId
        user_url = f"{FIRESTORE_REST_URL}/users/{user_id}?updateMask.fieldPaths=deviceId"
        requests.patch(
            user_url, 
            json={"fields": {"deviceId": {"stringValue": str(new_device_id)}}}, 
            headers=FirestoreService._headers(id_token)
        )

        # 3. Assign user as owner of the new device
        device_url = f"{FIRESTORE_REST_URL}/devices/{new_device_id}?updateMask.fieldPaths=ownerId"
        requests.patch(
            device_url, 
            json={"fields": {"ownerId": {"stringValue": str(user_id)}}}, 
            headers=FirestoreService._headers(id_token)
        )

    @staticmethod
    def update_pump_status(device_id, status, id_token):
        url = f"{FIRESTORE_REST_URL}/devices/{device_id}?updateMask.fieldPaths=pumpStatus&updateMask.fieldPaths=lastPumpTimestamp"
        body = {
            "fields": {
                "pumpStatus": {"stringValue": str(status)},
                "lastPumpTimestamp": {"stringValue": datetime.utcnow().isoformat()}
            }
        }
        requests.patch(url, json=body, headers=FirestoreService._headers(id_token))

    @staticmethod
    def get_device_data(device_id, id_token):
        url = f"{FIRESTORE_REST_URL}/devices/{device_id}"
        res = requests.get(url, headers=FirestoreService._headers(id_token)).json()
        if "fields" in res:
            fields = res["fields"]
            return {
                "waterLevel": fields.get("waterLevel", {}).get("stringValue", "EMPTY"),
                "pumpStatus": fields.get("pumpStatus", {}).get("stringValue", "OFF"),
                "lastPumpTimestamp": fields.get("lastPumpTimestamp", {}).get("stringValue", fields.get("lastUpdated", {}).get("stringValue", "N/A")),
                "lastFullTimestamp": fields.get("lastFullTimestamp", {}).get("stringValue", None)
            }
        return None

    @staticmethod
    def listen_to_device(device_id, id_token, on_update_callback, interval=2):
        stop_event = threading.Event()

        def poll():
            while not stop_event.is_set():
                try:
                    data = FirestoreService.get_device_data(device_id, id_token)
                    if data:
                        on_update_callback(data)
                except Exception:
                    pass
                time.sleep(interval)

        thread = threading.Thread(target=poll, daemon=True)
        thread.start()

        class ListenerSubscription:
            def unsubscribe(self):
                stop_event.set()

        return ListenerSubscription()