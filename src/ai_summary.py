import os
from datetime import date
from anthropic import Anthropic
from dotenv import load_dotenv
from src.database import sla_samenvatting_op

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def genereer_samenvatting(listings: list) -> str:
    """
    Vraagt Claude om een kort overzicht te schrijven van de net gevonden nieuwe listings.
    Wordt alleen aangeroepen als er ook echt nieuwe woningen zijn (scheelt tokens bij uurlijkse runs).
    """
    listings_tekst = _listings_naar_tekst(listings)
    prompt = _maak_prompt(listings_tekst, date.today().isoformat())

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    bericht = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    tekst = bericht.content[0].text

    sla_samenvatting_op(date.today().isoformat(), tekst)
    return tekst


def _listings_naar_tekst(listings: list) -> str:
    regels = []
    for l in listings:
        prijs = f"€{l['prijs']}/mnd" if l.get("prijs") else "prijs onbekend"
        opp = f"{l['oppervlakte']}m²" if l.get("oppervlakte") else ""
        kamers = f"{l['kamers']} kamers" if l.get("kamers") else ""
        details = ", ".join(filter(None, [prijs, opp, kamers]))
        regels.append(f"- {l.get('adres') or 'Adres onbekend'} ({details}) [{l['bron']}]")
    return "\n".join(regels)


def _maak_prompt(listings_tekst: str, datum: str) -> str:
    return f"""Je bent een assistent die de huurmarkt in Breda bijhoudt voor iemand die op zoek is naar een huurwoning.

Zojuist ({datum}) zijn de volgende nieuwe huurwoningen gevonden:

{listings_tekst}

Schrijf een kort, vriendelijk overzicht (maximaal 100 woorden) in het Nederlands:
- Hoeveel nieuwe woningen zijn er gevonden?
- Wat is het prijsbereik?
- Zijn er opvallende aanbiedingen (groot, goedkoop, of juist duur)?
- Sluit af met één aanmoedigende zin.

Schrijf alsof je een vriend bent die het even doorneemt, niet als een formeel rapport."""
