import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "")
WHATSAPP_APIKEY = os.getenv("WHATSAPP_APIKEY", "")


def stuur_nieuwe_woningen_whatsapp(listings: list):
    """Stuurt een WhatsApp-melding via CallMeBot over nieuwe woningen."""
    if not WHATSAPP_PHONE or not WHATSAPP_APIKEY:
        print("WhatsApp niet geconfigureerd (WHATSAPP_PHONE/WHATSAPP_APIKEY ontbreken) — overgeslagen.")
        return

    bericht = _maak_bericht(listings)
    url = (
        "https://api.callmebot.com/whatsapp.php"
        f"?phone={WHATSAPP_PHONE}&text={quote(bericht)}&apikey={WHATSAPP_APIKEY}"
    )
    resp = requests.get(url, timeout=15)
    print(f"WhatsApp verstuurd (status {resp.status_code})")


def _maak_bericht(listings: list) -> str:
    regels = [f"🏠 {len(listings)} nieuwe woning(en) in Breda!"]
    for l in listings:
        prijs = f"€{l['prijs']}/mnd" if l.get("prijs") else "prijs onbekend"
        opp = f", {l['oppervlakte']}m²" if l.get("oppervlakte") else ""
        regels.append(f"\n📍 {l.get('adres') or 'Adres onbekend'} — {prijs}{opp}")
        if l.get("link"):
            regels.append(l["link"])
    return "\n".join(regels)
