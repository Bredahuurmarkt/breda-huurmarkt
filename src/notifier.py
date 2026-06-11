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
    kaarten = ""
    for l in listings:
        prijs = f"€ {l['prijs']:,}".replace(",", ".") + " /mnd" if l.get("prijs") else "prijs onbekend"
        details = " · ".join(filter(None, [
            f"{l['oppervlakte']} m²" if l.get("oppervlakte") else None,
            f"{l['kamers']} kamers" if l.get("kamers") else None,
            l.get("bron", "").capitalize() or None,
        ]))
        link = l.get("link", "#")
        adres = l.get("adres") or "Adres onbekend"
        foto = l.get("foto_url") or ""
        foto_html = (
            f'<img src="{foto}" alt="{adres}" width="640" '
            f'style="display:block; width:100%; max-height:260px; object-fit:cover;">'
            if foto else ""
        )
        kaarten += f"""
    <div style="border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; margin:0 0 20px 0; background:#ffffff;">
        {foto_html}
        <div style="padding:16px 20px;">
            <p style="margin:0 0 4px 0; font-size:18px; font-weight:bold; color:#1a202c;">{adres}</p>
            <p style="margin:0 0 4px 0; font-size:17px; color:#2b6cb0; font-weight:bold;">{prijs}</p>
            <p style="margin:0 0 12px 0; font-size:14px; color:#718096;">{details}</p>
            <a href="{link}" style="display:inline-block; background:#2b6cb0; color:#ffffff; text-decoration:none;
               padding:10px 22px; border-radius:8px; font-size:14px; font-weight:bold;">Bekijk woning →</a>
        </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="nl">
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; padding: 20px; background:#f7fafc;">
    <h1 style="color: #2c5282;">🏠 Breda Huurmarkt — {datum}</h1>
    <div style="background: #ebf8ff; border-left: 4px solid #4299e1; padding: 16px; margin: 20px 0; border-radius:0 8px 8px 0;">
        <p style="margin:0; white-space: pre-wrap;">{samenvatting}</p>
    </div>
    <h2 style="color: #2d3748;">Nieuwe woningen ({len(listings)})</h2>
    {kaarten}
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
