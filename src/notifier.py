import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from dotenv import load_dotenv

load_dotenv()

NOTIFY_FROM = os.getenv("NOTIFY_FROM", "")
NOTIFY_TO = os.getenv("NOTIFY_TO", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def stuur_dagelijks_overzicht(samenvatting: str, nieuwe_listings: list, datum: str | None = None):
    """Stuurt het dagelijkse overzicht via Gmail SMTP."""
    if not GMAIL_APP_PASSWORD:
        print("GMAIL_APP_PASSWORD niet ingesteld — e-mail overgeslagen.")
        return

    if datum is None:
        datum = date.today().strftime("%d %B %Y")

    onderwerp = f"🏠 Breda Huurmarkt — {len(nieuwe_listings)} nieuwe woning(en)"
    html_body = _maak_html(samenvatting, nieuwe_listings, datum)
    tekst_body = _maak_tekst(samenvatting, nieuwe_listings)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = onderwerp
    msg["From"] = NOTIFY_FROM
    msg["To"] = NOTIFY_TO
    msg.attach(MIMEText(tekst_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(NOTIFY_FROM, GMAIL_APP_PASSWORD)
        server.sendmail(NOTIFY_FROM, NOTIFY_TO, msg.as_string())

    print(f"E-mail verstuurd naar {NOTIFY_TO}")


def _maak_html(samenvatting: str, listings: list, datum: str) -> str:
    listing_rijen = ""
    for l in listings:
        prijs = f"€{l['prijs']}/mnd" if l.get("prijs") else "—"
        opp = f"{l['oppervlakte']} m²" if l.get("oppervlakte") else "—"
        kamers = str(l["kamers"]) if l.get("kamers") else "—"
        link = l.get("link", "#")
        adres = l.get("adres") or "Adres onbekend"
        listing_rijen += f"""
        <tr>
            <td><a href="{link}">{adres}</a></td>
            <td>{prijs}</td>
            <td>{opp}</td>
            <td>{kamers}</td>
            <td>{l['bron']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="nl">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
    <h1 style="color: #2c5282;">🏠 Breda Huurmarkt — {datum}</h1>
    <div style="background: #ebf8ff; border-left: 4px solid #4299e1; padding: 16px; margin: 20px 0;">
        <p style="margin:0; white-space: pre-wrap;">{samenvatting}</p>
    </div>
    <h2 style="color: #2d3748;">Nieuwe woningen ({len(listings)})</h2>
    <table style="width:100%; border-collapse:collapse;">
        <thead>
            <tr style="background:#2c5282; color:white;">
                <th style="padding:8px; text-align:left;">Adres</th>
                <th style="padding:8px;">Prijs</th>
                <th style="padding:8px;">Opp.</th>
                <th style="padding:8px;">Kamers</th>
                <th style="padding:8px;">Bron</th>
            </tr>
        </thead>
        <tbody>{listing_rijen}</tbody>
    </table>
    <p style="color:#718096; font-size:12px; margin-top:30px;">
        Breda Huurmarkt Monitor — automatisch gegenereerd
    </p>
</body>
</html>"""


def _maak_tekst(samenvatting: str, listings: list) -> str:
    regels = [samenvatting, "", f"Nieuwe woningen ({len(listings)}):", "-" * 40]
    for l in listings:
        prijs = f"€{l['prijs']}/mnd" if l.get("prijs") else "prijs onbekend"
        regels.append(f"{l.get('adres') or 'Onbekend'} — {prijs} [{l['bron']}]")
        if l.get("link"):
            regels.append(f"  {l['link']}")
    return "\n".join(regels)
