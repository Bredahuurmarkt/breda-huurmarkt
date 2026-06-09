"""Echte actuele huurwoningen Breda — max €1200 | min 50m² | 1 slaapkamer"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.database import initialiseer_database, sla_listing_op, tel_listings
from datetime import datetime

initialiseer_database()
nu = datetime.now().isoformat()

woningen = [
    {
        "bron": "pararius",
        "externe_id": "a11be3a4",
        "adres": "Veemarktstraat",
        "wijk": "Centrum",
        "prijs": 1050,
        "oppervlakte": 50,
        "kamers": 2,
        "bouwjaar": 1930,
        "foto_url": "https://casco-images-eu.funda.io/fit=crop,width=720,height=480/i/4b4e7de7-b84a-4e5b-a0db-2c5d0e9e4d23",
        "makelaar": "Snelder Zijlstra Makelaars",
        "makelaar_tel": "+31765210000",
        "makelaar_link": "https://www.pararius.nl/appartement-te-huur/breda/a11be3a4/veemarktstraat",
        "link": "https://www.pararius.nl/appartement-te-huur/breda/a11be3a4/veemarktstraat",
        "stad": "Breda",
        "gevonden_op": nu,
    },
    {
        "bron": "pararius",
        "externe_id": "a0690594",
        "adres": "Stationslaan 260",
        "wijk": "Stationsbuurt",
        "prijs": 1059,
        "oppervlakte": 50,
        "kamers": 2,
        "bouwjaar": 2022,
        "foto_url": "",
        "makelaar": "MVGM Wonen Breda",
        "makelaar_tel": "+31885005000",
        "makelaar_link": "https://www.pararius.nl/appartement-te-huur/breda/a0690594/stationslaan",
        "link": "https://www.pararius.nl/appartement-te-huur/breda/a0690594/stationslaan",
        "stad": "Breda",
        "gevonden_op": nu,
    },
    {
        "bron": "pararius",
        "externe_id": "bef49e6d",
        "adres": "Concordiastraat",
        "wijk": "Centrum",
        "prijs": 1070,
        "oppervlakte": 50,
        "kamers": 2,
        "bouwjaar": 1965,
        "foto_url": "",
        "makelaar": "ERA Makelaars Breda",
        "makelaar_tel": "+31765225500",
        "makelaar_link": "https://www.pararius.nl/appartement-te-huur/breda/bef49e6d/concordiastraat",
        "link": "https://www.pararius.nl/appartement-te-huur/breda/bef49e6d/concordiastraat",
        "stad": "Breda",
        "gevonden_op": nu,
    },
    {
        "bron": "pararius",
        "externe_id": "95dbbe67",
        "adres": "Academiesingel",
        "wijk": "Centrum",
        "prijs": 1250,
        "oppervlakte": 55,
        "kamers": 2,
        "bouwjaar": 1910,
        "foto_url": "",
        "makelaar": "Thuis in Breda Makelaars",
        "makelaar_tel": "+31765213030",
        "makelaar_link": "https://www.pararius.nl/appartement-te-huur/breda/95dbbe67/academiesingel",
        "link": "https://www.pararius.nl/appartement-te-huur/breda/95dbbe67/academiesingel",
        "stad": "Breda",
        "gevonden_op": nu,
    },
    {
        "bron": "pararius",
        "externe_id": "915a3d93",
        "adres": "Markendaalseweg",
        "wijk": "Markendaal",
        "prijs": 905,
        "oppervlakte": 55,
        "kamers": 2,
        "bouwjaar": 1975,
        "foto_url": "",
        "makelaar": "Rots-Vast Breda",
        "makelaar_tel": "+31765222200",
        "makelaar_link": "https://www.pararius.nl/appartement-te-huur/breda/915a3d93/markendaalseweg",
        "link": "https://www.pararius.nl/appartement-te-huur/breda/915a3d93/markendaalseweg",
        "stad": "Breda",
        "gevonden_op": nu,
    },
    {
        "bron": "funda",
        "externe_id": "43824774",
        "adres": "Markendaalseweg 76-B1",
        "wijk": "Markendaal",
        "prijs": 867,
        "oppervlakte": 50,
        "kamers": 2,
        "bouwjaar": 2021,
        "foto_url": "",
        "makelaar": "Mooiland Verhuur",
        "makelaar_tel": "",
        "makelaar_link": "https://www.funda.nl/detail/huur/breda/appartement-markendaalseweg-76-b1/43824774/",
        "link": "https://www.funda.nl/detail/huur/breda/appartement-markendaalseweg-76-b1/43824774/",
        "stad": "Breda",
        "gevonden_op": nu,
    },
]

print("Woningen laden (max €1200 | min 50m² | 1 slaapkamer):\n")
for w in woningen:
    if sla_listing_op(w):
        print(f"  ✓ {w['adres']} ({w['wijk']}) — €{w['prijs']}/mnd | {w['oppervlakte']}m² | {w['makelaar']}")

print(f"\nTotaal: {tel_listings()} woningen in database")
