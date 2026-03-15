import firebase_admin
from firebase_admin import credentials, db
import os

private_key = os.getenv("FIREBASE_PRIVATE_KEY")

cred_dict = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key": private_key.replace("\\n", "\n") if private_key else None,
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "token_uri": "https://oauth2.googleapis.com/token",
}

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": os.getenv("FIREBASE_DB_URL")
        }
    )

def get_db_ref(path: str):
    return db.reference(path)