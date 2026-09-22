# firebase_config.py
# Replace with your actual Firebase Project ID and Web API Key from Firebase Console

FIREBASE_PROJECT_ID = "water-storage-controller"
FIREBASE_WEB_API_KEY = "AIzaSyCvZW0AEZM7JrDG71_UgRBw4zv_1__YR0o"

# Authentication Endpoints
AUTH_SIGN_IN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
AUTH_SIGN_UP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
AUTH_SEND_EMAIL_VERIFICATION_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"
AUTH_GET_USER_INFO_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_WEB_API_KEY}"
AUTH_CREATE_USER_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
AUTH_PASSWORD_RESET_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"

# Firestore REST Base URL (Android client-safe)
FIRESTORE_REST_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"
