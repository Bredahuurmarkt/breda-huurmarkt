"""
Parser voor Google Alerts e-mails.
Google stuurt een HTML-mail met een lijst van nieuwe zoekresultaten.
Wij halen daaruit: titel, url, beschrijving, datum.
"""
import re
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime


def parseer_google_alert(mail: dict) -> list:
    soup = BeautifulSoup(mail["body"], "html.parser")
    listings = []

    # Google Alerts structuur: elk resultaat zit in een <td> met een <a> link
    for link_tag in soup.find_all("a", href=True):
        href = link_tag.get("href", "")

        # Google wraps links in een redirect URL — haal echte URL eruit
        echte_url = _extraheer_echte_url(href)
        if not echte_url:
            continue

        # Alleen Breda-gerelateerde links
        tekst = link_tag.get_text(" ", strip=True)
        container = link_tag.find_parent(["td", "div", "li"])
        omschrijving = container.get_text(" ", strip=True)[:200] if container else tekst[:200]

        if not tekst or len(tekst) < 5:
            continue

        listings.append({
            "bron": "google_alerts",
            "externe_id": _maak_id(echte_url),
            "adres": tekst[:80],
            "stad": "Breda",
            "prijs": None,
            "oppervlakte": None,
            "kamers": None,
            "link": echte_url,
            "omschrijving": omschrijving,
            "gevonden_op": _parseer_datum(mail.get("datum", "")),
        })

    return listings


def _extraheer_echte_url(google_url: str) -> str | None:
    """Google Alerts omhult links in een /url?q=... redirect."""
    match = re.search(r"[?&]q=([^&]+)", google_url)
    if match:
        from urllib.parse import unquote
        return unquote(match.group(1))
    # Soms is het gewoon een directe URL
    if google_url.startswith("http") and "google.com" not in google_url:
        return google_url
    return None


def _parseer_datum(datum_str: str) -> str:
    try:
        return parsedate_to_datetime(datum_str).isoformat()
    except Exception:
        return datetime.now().isoformat()


def _maak_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]
