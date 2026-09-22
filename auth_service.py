import requests
from firebase_config import (
    AUTH_SIGN_IN_URL,
    AUTH_SIGN_UP_URL,
    AUTH_SEND_EMAIL_VERIFICATION_URL,
    AUTH_GET_USER_INFO_URL,
    FIREBASE_WEB_API_KEY,
)

AUTH_PASSWORD_RESET_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"

class AuthService:
    @staticmethod
    def send_password_reset_email(email):
        """Sends the password reset email."""
        clean_email = email.strip().lower()
        payload = {"requestType": "PASSWORD_RESET", "email": clean_email}
        res = requests.post(AUTH_PASSWORD_RESET_URL, json=payload).json()
        if "error" in res:
            err_msg = res["error"]["message"]
            if err_msg == "EMAIL_NOT_FOUND":
                raise Exception("User does not exist. Sign up please.")
            raise Exception(err_msg)
        return res

    @staticmethod
    def sign_up(email, password):
        clean_email = email.strip().lower()
        payload = {"email": clean_email, "password": password, "returnSecureToken": True}
        res = requests.post(AUTH_SIGN_UP_URL, json=payload).json()
        if "error" in res:
            err_msg = res["error"]["message"]
            if "EMAIL_EXISTS" in err_msg:
                raise Exception("An account with this email already exists. Please Log in.")
            raise Exception(err_msg)
        
        # Send verification email link immediately
        AuthService.send_verification_email(res["idToken"])
        return res

    @staticmethod
    def send_verification_email(id_token):
        payload = {"requestType": "VERIFY_EMAIL", "idToken": id_token}
        res = requests.post(AUTH_SEND_EMAIL_VERIFICATION_URL, json=payload).json()
        if "error" in res:
            raise Exception(res["error"]["message"])
        return res

    @staticmethod
    def sign_in(email, password):
        clean_email = email.strip().lower()
        payload = {"email": clean_email, "password": password, "returnSecureToken": True}
        res = requests.post(AUTH_SIGN_IN_URL, json=payload).json()
        
        if "error" in res:
            err_code = res["error"].get("message", "")
            
            if err_code in ["EMAIL_NOT_FOUND", "INVALID_EMAIL"]:
                raise Exception("User does not exist. Sign up please.")
            elif err_code == "INVALID_PASSWORD":
                raise Exception("Wrong password.")
            elif err_code == "USER_DISABLED":
                raise Exception("This account has been disabled.")
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in err_code:
                raise Exception("Too many failed attempts. Please try again later.")
            else:
                # If protection is still active in console, fallback to user not found check
                raise Exception(err_code)
        
        # Check if email is verified
        user_info = AuthService.get_user_info(res["idToken"])
        if not user_info.get("emailVerified", False):
            raise Exception("Please verify your account using the link sent to your email.")
            
        return res

    @staticmethod
    def get_user_info(id_token):
        payload = {"idToken": id_token}
        res = requests.post(AUTH_GET_USER_INFO_URL, json=payload).json()
        if "error" in res:
            raise Exception(res["error"]["message"])
        return res["users"][0]