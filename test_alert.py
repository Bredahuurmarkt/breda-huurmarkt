"""
End-to-end test: stuurt een echte alert-mail (ikwilhuren.nu formaat) naar de inbox,
leest hem daarna uit via Gmail, parseert hem en slaat de woning op.
Dit bewijst de volledige pijplijn ZONDER verzonnen data — alle gegevens
komen uit de echte ikwilhuren.nu-pagina.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

from src.gmail_reader import _get_service, haal_mail_inhoud_op, markeer_als_gelezen
from src.parser import verwerk_mail
from src.database import initialiseer_database, sla_listing_op, tel_listings

load_dotenv()
FROM = os.getenv("NOTIFY_FROM")
TO = os.getenv("NOTIFY_TO")
WACHTWOORD = os.getenv("GMAIL_APP_PASSWORD")

ONDERWERP = "Nieuwe huurwoning in Breda — TEST ALERT"

# Echte gegevens, opgehaald van de ikwilhuren.nu pagina
FOTO = "https://ikwilhuren.nu/media/fd/fd6517725a684882a551f393d174551e/1600/terheijdenstraat-102-340-breda-2596-bpl-abe-van-ancum-fotografie-01.jpg"
LINK = "https://ikwilhuren.nu/object/breda-4816bx-202-terheijdenstraat-f0be3637b8305fb40bcd9d8ee0bf4db5/"

HTML = f"""<!DOCTYPE html>
<html><body>
  <h2>Nieuw aanbod dat past bij jouw zoekopdracht</h2>
  <table>
    <tr><td>
      <a href="{LINK}">
        <img src="{FOTO}" width="400">
        <div>Terheijdenstraat 202, Breda</div>
      </a>
      <div>Huurprijs: &euro; 1.200 per maand</div>
      <div>Oppervlakte: 75 m&sup2;</div>
      <div>2 slaapkamers</div>
      <div>Aangeboden door MVGM Breda — tel. +31 88 43 24 700</div>
    </td></tr>
  </table>
</body></html>"""


def stuur_test_mail():
    msg = MIMEMultipart("alternative")
    msg["Subject"] = ONDERWERP
    msg["From"] = FROM
    msg["To"] = TO
    msg.attach(MIMEText("Nieuwe huurwoning Terheijdenstraat 202 Breda", "plain", "utf-8"))
    msg.attach(MIMEText(HTML, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(FROM, WACHTWOORD)
        s.sendmail(FROM, TO, msg.as_string())
    print("1. Test-alertmail verstuurd naar de inbox.")


def verwerk():
    service = _get_service()
    # Zoek de net verstuurde mail op onderwerp
    res = service.users().messages().list(
        userId="me", q=f'subject:"{ONDERWERP}" is:unread', maxResults=5
    ).execute()
    berichten = res.get("messages", [])
    if not berichten:
        print("   Mail nog niet gevonden — even wachten en opnieuw proberen...")
        return False

    print(f"2. Mail gevonden in inbox ({len(berichten)} stuks). Inhoud ophalen...")
    initialiseer_database()
    nieuw = 0
    for b in berichten:
        mail = haal_mail_inhoud_op(b["id"])
        listings = verwerk_mail(mail)
        print(f"3. Parser haalde {len(listings)} woning(en) uit de mail:")
        for l in listings:
            print(f"     • {l['adres']} — €{l['prijs']}/mnd | {l['oppervlakte']}m² | {l['makelaar']} {l['makelaar_tel']}")
            print(f"       foto: {l['foto_url'][:60]}...")
            if sla_listing_op(l):
                nieuw += 1
        markeer_als_gelezen(b["id"])
    print(f"4. {nieuw} woning(en) opgeslagen in database. Totaal nu: {tel_listings()}")
    return True


if __name__ == "__main__":
    stuur_test_mail()
    print("   Even wachten tot de mail binnen is...")
    for poging in range(6):
        time.sleep(5)
        if verwerk():
            break
    else:
        print("Mail kon niet worden gevonden. Probeer test_alert.py nogmaals.")
    print("\nKlaar! Bekijk het resultaat op https://breda-huurmarkt.streamlit.app")
