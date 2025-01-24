# constants.py

from config import settings

MEGAPLAN_API_URL = settings.MEGAPLAN_API_URL
MEGAPLAN_API_KEY = settings.MEGAPLAN_API_KEY
MEGAPLAN_HEADER = {
    "Authorization": f"Bearer {MEGAPLAN_API_KEY}",
    "Content-Type": "application/json"
}
