import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def stuur_nieuwe_woningen_telegram(listings: list):
    """Stuurt een Telegram-melding over nieuwe woningen."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram niet geconfigureerd (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ontbreken) — overgeslagen.")
        return

    bericht = _maak_bericht(listings)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": bericht,
        "disable_web_page_preview": False,
    }, timeout=15)
    print(f"Telegram verstuurd (status {resp.status_code})")


def _maak_bericht(listings: list) -> str:
    regels = [f"🏠 {len(listings)} nieuwe woning(en) in Breda!"]
    for l in listings:
        prijs = f"€{l['prijs']}/mnd" if l.get("prijs") else "prijs onbekend"
        opp = f", {l['oppervlakte']}m²" if l.get("oppervlakte") else ""
        regels.append(f"\n📍 {l.get('adres') or 'Adres onbekend'} — {prijs}{opp}")
        if l.get("link"):
            regels.append(l["link"])
    return "\n".join(regels)
