import firebase_admin
from firebase_admin import credentials, db
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
cred_path = BASE_DIR / "firebase_key.json"

if not cred_path.exists():
    raise FileNotFoundError(f"Firebase key not found at {cred_path}")

if not firebase_admin._apps:
    cred = credentials.Certificate(str(cred_path))
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://healthwatch-iot-default-rtdb.asia-southeast1.firebasedatabase.app/"
        }
    )

def get_db_ref(path: str):
    return db.reference(path)