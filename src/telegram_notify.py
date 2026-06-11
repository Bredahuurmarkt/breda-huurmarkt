import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def stuur_nieuwe_woningen_telegram(listings: list):
    """Stuurt een Telegram-melding over nieuwe woningen: een kop-bericht en
    daarna per woning een foto met onderschrift (of tekst als er geen foto is)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram niet geconfigureerd (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ontbreken) — overgeslagen.")
        return

    basis = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    requests.post(f"{basis}/sendMessage", json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🏠 {len(listings)} nieuwe woning(en) in Breda!",
    }, timeout=15)

    verstuurd = 0
    for l in listings:
        caption = _maak_caption(l)
        foto = l.get("foto_url") or ""
        resp = None
        if foto:
            resp = requests.post(f"{basis}/sendPhoto", json={
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": foto,
                "caption": caption,
            }, timeout=20)
        if resp is None or resp.status_code != 200:
            # Geen foto, of Telegram kon de foto-URL niet laden → gewoon als tekst
            resp = requests.post(f"{basis}/sendMessage", json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": caption,
                "disable_web_page_preview": False,
            }, timeout=15)
        if resp.status_code == 200:
            verstuurd += 1

    print(f"Telegram verstuurd ({verstuurd}/{len(listings)} woning(en))")


def _maak_caption(l: dict) -> str:
    prijs = f"€{l['prijs']}/mnd" if l.get("prijs") else "prijs onbekend"
    details = " · ".join(filter(None, [
        f"{l['oppervlakte']}m²" if l.get("oppervlakte") else None,
        f"{l['kamers']} kamers" if l.get("kamers") else None,
        (l.get("bron") or "").capitalize() or None,
    ]))
    regels = [f"📍 {l.get('adres') or 'Adres onbekend'} — {prijs}"]
    if details:
        regels.append(details)
    if l.get("link"):
        regels.append(l["link"])
    return "\n".join(regels)


def stuur_ochtendcheck(aantal_listings: int):
    """Stuurt een kort dagelijks statusbericht, ook als er geen nieuwe woningen zijn —
    zodat duidelijk is dat de pipeline draait."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram niet geconfigureerd (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ontbreken) — overgeslagen.")
        return

    bericht = (
        f"✅ Goedemorgen! Pipeline draait.\n"
        f"Geen nieuwe woningen vandaag (nog).\n"
        f"{aantal_listings} actieve woning(en) in de database."
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": bericht,
    }, timeout=15)
    print(f"Ochtendcheck verstuurd (status {resp.status_code})")


