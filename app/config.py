import os
from dotenv import load_dotenv

load_dotenv()

SALLA_BASE_URL = "https://api.salla.dev/admin/v2"
SALLA_ACCESS_TOKEN = os.getenv("SALLA_ACCESS_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-this-secret")

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
AUTO_ADD_ORDER_NOTE = os.getenv("AUTO_ADD_ORDER_NOTE", "false").lower() == "true"
PORT = int(os.getenv("PORT", "8000"))
