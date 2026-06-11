import re
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup


def verwerk_mail(mail: dict) -> list:
    """
    Zet een ruwe mail (output van haal_mail_inhoud_op) om naar een lijst listings.
    Detecteert automatisch de bron op basis van afzender.
    """
    afzender = mail.get("afzender", "").lower()

    if "pararius" in afzender:
        return _parseer_pararius(mail)
    elif "funda" in afzender:
        return _parseer_funda(mail)
    elif "huurwoningen" in afzender:
        return _parseer_huurwoningen(mail)
    elif "google" in afzender and "alerts" in mail.get("onderwerp", "").lower():
        from src.parser_google_alerts import parseer_google_alert
        return parseer_google_alert(mail)
    elif "rentumo" in afzender:
        return _parseer_rentumo(mail)
    elif "huizenvinder" in afzender:
        return _parseer_generiek(mail, "huizenvinder", r"huizenvinder\.nl")
    elif "huurportaal" in afzender:
        return _parseer_generiek(mail, "huurportaal", r"huurportaal\.nl")
    elif "ikwilhuren" in afzender or "ikwilhuren.nu" in mail.get("body", ""):
        return _parseer_ikwilhuren(mail)
    else:
        return []


def _parseer_pararius(mail: dict) -> list:
    soup = BeautifulSoup(mail["body"], "html.parser")
    listings = []

    # Pararius stuurt meerdere woningen per mail, elk in een eigen blok
    # Zoek op bekende CSS-klassen of patroon van links + tekst
    for link_tag in soup.find_all("a", href=re.compile(r"pararius\.nl/huurwoningen")):
        href = link_tag.get("href", "")
        tekst = link_tag.get_text(" ", strip=True)

        # Adres staat meestal in de link-tekst of een bovenliggende container
        container = link_tag.find_parent(["td", "div", "li", "tr"])
        container_tekst = container.get_text(" ", strip=True) if container else tekst

        listings.append({
            "bron": "pararius",
            "externe_id": _maak_id(href),
            "adres": _extraheer_adres(container_tekst) or tekst[:80],
            "stad": "Breda",
            "prijs": _extraheer_prijs(container_tekst),
            "oppervlakte": _extraheer_oppervlakte(container_tekst),
            "kamers": _extraheer_kamers(container_tekst),
            "link": href,
            "gevonden_op": _parseer_datum(mail.get("datum", "")),
        })

    return listings


def _parseer_funda(mail: dict) -> list:
    soup = BeautifulSoup(mail["body"], "html.parser")
    listings = []

    for link_tag in soup.find_all("a", href=re.compile(r"funda\.nl/huur")):
        href = link_tag.get("href", "")
        container = link_tag.find_parent(["td", "div", "li", "tr"])
        container_tekst = container.get_text(" ", strip=True) if container else ""

        listings.append({
            "bron": "funda",
            "externe_id": _maak_id(href),
            "adres": _extraheer_adres(container_tekst),
            "stad": "Breda",
            "prijs": _extraheer_prijs(container_tekst),
            "oppervlakte": _extraheer_oppervlakte(container_tekst),
            "kamers": _extraheer_kamers(container_tekst),
            "link": href,
            "gevonden_op": _parseer_datum(mail.get("datum", "")),
        })

    return listings


def _parseer_huurwoningen(mail: dict) -> list:
    soup = BeautifulSoup(mail["body"], "html.parser")
    listings = []

    for link_tag in soup.find_all("a", href=re.compile(r"huurwoningen\.nl")):
        href = link_tag.get("href", "")
        container = link_tag.find_parent(["td", "div", "li", "tr"])
        container_tekst = container.get_text(" ", strip=True) if container else ""

        listings.append({
            "bron": "huurwoningen",
            "externe_id": _maak_id(href),
            "adres": _extraheer_adres(container_tekst),
            "stad": "Breda",
            "prijs": _extraheer_prijs(container_tekst),
            "oppervlakte": _extraheer_oppervlakte(container_tekst),
            "kamers": _extraheer_kamers(container_tekst),
            "link": href,
            "gevonden_op": _parseer_datum(mail.get("datum", "")),
        })

    return listings


def _extraheer_prijs(tekst: str) -> int | None:
    """Haalt het maandbedrag in euro op uit tekst. Bijv: '€ 1.250 /maand' → 1250"""
    match = re.search(r"€\s*([\d.,]+)", tekst)
    if match:
        bedrag = match.group(1).replace(".", "").replace(",", "")
        try:
            return int(bedrag)
        except ValueError:
            return None
    return None


def _extraheer_oppervlakte(tekst: str) -> int | None:
    """Haalt oppervlakte in m² op. Bijv: '75 m²' → 75"""
    match = re.search(r"(\d+)\s*m[²2]", tekst, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extraheer_kamers(tekst: str) -> int | None:
    """Haalt aantal kamers op. Bijv: '3 kamers' → 3"""
    match = re.search(r"(\d+)\s*kamer", tekst, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extraheer_adres(tekst: str) -> str | None:
    """Ruwe adresextractie: eerste zin of regel die op een adres lijkt."""
    # Kijk naar patronen als "Straatnaam 12" of "Straatnaam 12a"
    match = re.search(r"([A-Z][a-zÀ-ÿ]+(?:straat|laan|weg|plein|singel|kade|gracht|dijk|park|hof|ring|steeg|dreef|buurt|erf|pad|dam|markt|berg|veld|baan)[^\d]*\d+\w?)", tekst)
    if match:
        return match.group(1).strip()
    # Fallback: eerste 60 tekens
    regels = [r.strip() for r in tekst.split("\n") if r.strip()]
    return regels[0][:60] if regels else None


def _parseer_datum(datum_str: str) -> str:
    """Zet een e-maildatum (RFC 2822) om naar ISO 8601."""
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(datum_str).isoformat()
    except Exception:
        return datetime.now().isoformat()


def _maak_id(url: str) -> str:
    """Maakt een korte unieke ID op basis van de URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _parseer_ikwilhuren(mail: dict) -> list:
    """Parser voor ikwilhuren.nu alert-mails. Haalt adres, prijs, m², foto en makelaar op."""
    soup = BeautifulSoup(mail["body"], "html.parser")
    listings = []
    gezien = set()

    for link_tag in soup.find_all("a", href=re.compile(r"ikwilhuren\.nu/object")):
        href = link_tag.get("href", "")
        if href in gezien:
            continue
        gezien.add(href)

        container = link_tag.find_parent(["td", "div", "li", "tr", "article", "table"])
        tekst = container.get_text(" ", strip=True) if container else link_tag.get_text(" ", strip=True)

        # Foto: zoek een img binnen de container
        foto_url = ""
        if container:
            img = container.find("img")
            if img and img.get("src"):
                foto_url = img["src"]
                if foto_url.startswith("/"):
                    foto_url = "https://ikwilhuren.nu" + foto_url

        # Makelaar + telefoon uit de tekst halen (als aanwezig)
        makelaar = ""
        m_mak = re.search(r"(MVGM|Rots-?Vast|Vesteda|Bouwinvest|[A-Z][a-z]+\s+Makelaars?)", tekst)
        if m_mak:
            makelaar = m_mak.group(1).strip()
        makelaar_tel = ""
        m_tel = re.search(r"(\+?31\s?\d[\d\s]{7,})", tekst)
        if m_tel:
            makelaar_tel = re.sub(r"\s+", "", m_tel.group(1))

        listings.append({
            "bron": "ikwilhuren",
            "externe_id": _maak_id(href),
            "adres": _extraheer_adres(tekst) or link_tag.get_text(strip=True)[:80],
            "stad": "Breda",
            "prijs": _extraheer_prijs(tekst),
            "oppervlakte": _extraheer_oppervlakte(tekst),
            "kamers": _extraheer_kamers(tekst),
            "foto_url": foto_url,
            "makelaar": makelaar,
            "makelaar_tel": makelaar_tel,
            "makelaar_link": href,
            "link": href,
            "gevonden_op": _parseer_datum(mail.get("datum", "")),
        })

    return listings


def _rentumo_adres_van_slug(slug: str) -> str:
    """Maakt een leesbaar adres van een Rentumo URL-slug, bijv.
    'te-huur-appartement-handellaan-88-in-breda-525657' -> 'Handellaan 88'."""
    s = re.sub(r"-\d+$", "", slug)  # interne advertentie-ID eraf
    s = re.sub(r"^te-huur-appartement-", "", s)
    s = re.sub(r"^te-huur-", "", s)
    s = re.sub(r"-in-breda$", "", s)
    s = re.sub(r"-breda$", "", s)
    s = re.sub(r"-\d{4}-[a-z]{2}$", "", s)  # postcode eraf
    return s.replace("-", " ").title()


def _parseer_rentumo(mail: dict) -> list:
    """
    Parser voor Rentumo alert-mails.

    Rentumo verstuurt links via een Mailchimp-trackingredirect
    (go.getrentumo.nl/CL0/<urlencoded-doel-url>/<volgnummer>/...) waarbij hetzelfde
    listing meerdere keren met een ander volgnummer voorkomt. We dedupliceren daarom
    op de slug van de daadwerkelijke advertentie i.p.v. de volledige trackinglink, en
    leiden het adres af uit die slug omdat de omringende teksten vaak afgekapt zijn.
    """
    soup = BeautifulSoup(mail["body"], "html.parser")
    listings = []
    gezien = set()

    for link_tag in soup.find_all("a", href=re.compile(r"getrentumo\.nl")):
        href = link_tag.get("href", "")
        match = re.search(r"advertentie%2F([a-zA-Z0-9\-]+)", href)
        if not match:
            continue
        slug = match.group(1)
        if slug in gezien:
            continue
        gezien.add(slug)

        # Zoek de eerste bovenliggende container met een prijs erin
        container_tekst = ""
        container = None
        node = link_tag
        for _ in range(10):
            node = node.parent
            if node is None:
                break
            tekst = node.get_text(" ", strip=True)
            if "€" in tekst and len(tekst) < 150:
                container_tekst = tekst
                container = node
                break

        prijs = _extraheer_prijs(container_tekst)
        if not prijs:
            continue  # Geen prijs = geen echte listing (bijv. de "bekijk je matches"-link)

        foto_url = ""
        if container:
            img = container.find("img")
            if img and img.get("src"):
                foto_url = img["src"]

        listings.append({
            "bron": "rentumo",
            "externe_id": _maak_id(slug),
            "adres": _rentumo_adres_van_slug(slug),
            "stad": "Breda",
            "prijs": prijs,
            "oppervlakte": _extraheer_oppervlakte(container_tekst),
            "kamers": _extraheer_kamers(container_tekst),
            "foto_url": foto_url,
            "link": f"https://rentumo.nl/advertentie/{slug}",
            "gevonden_op": _parseer_datum(mail.get("datum", "")),
        })

    return listings


def _parseer_generiek(mail: dict, bron: str, url_patroon: str) -> list:
    """
    Generieke parser voor nieuwe platforms.
    Zoekt op links die matchen met url_patroon en haalt prijs/oppervlakte uit de omgeving.
    Wordt later verfijnd zodra we echte alert-mails hebben gezien.
    """
    soup = BeautifulSoup(mail["body"], "html.parser")
    listings = []
    gezien = set()

    for link_tag in soup.find_all("a", href=re.compile(url_patroon)):
        href = link_tag.get("href", "")
        if href in gezien:
            continue
        gezien.add(href)

        container = link_tag.find_parent(["td", "div", "li", "tr", "article"])
        container_tekst = container.get_text(" ", strip=True) if container else link_tag.get_text(" ", strip=True)

        # Sla welkomstmails / niet-listing links over
        tekst_lower = container_tekst.lower()
        if any(woord in tekst_lower for woord in ["welkom", "registreer", "inloggen", "bevestig", "password", "wachtwoord"]):
            continue

        prijs = _extraheer_prijs(container_tekst)
        if not prijs:
            continue  # Geen prijs = waarschijnlijk geen listing

        listings.append({
            "bron": bron,
            "externe_id": _maak_id(href),
            "adres": _extraheer_adres(container_tekst),
            "stad": "Breda",
            "prijs": prijs,
            "oppervlakte": _extraheer_oppervlakte(container_tekst),
            "kamers": _extraheer_kamers(container_tekst),
            "link": href,
            "gevonden_op": _parseer_datum(mail.get("datum", "")),
        })

    return listings
