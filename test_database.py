from src.database import initialiseer_database, sla_listing_op, haal_listings_op, tel_listings
from datetime import datetime

initialiseer_database()

testdata = [
    {"bron": "pararius", "externe_id": "test001", "adres": "Ginnekenstraat 45", "prijs": 1200, "oppervlakte": 72, "kamers": 3, "link": "https://pararius.nl/test1", "gevonden_op": datetime.now().isoformat()},
    {"bron": "funda",    "externe_id": "test002", "adres": "Wilhelminasingel 12b", "prijs": 950, "oppervlakte": 55, "kamers": 2, "link": "https://funda.nl/test2", "gevonden_op": datetime.now().isoformat()},
    {"bron": "pararius", "externe_id": "test003", "adres": "Haagweg 88", "prijs": 1450, "oppervlakte": 90, "kamers": 4, "link": "https://pararius.nl/test3", "gevonden_op": datetime.now().isoformat()},
    # Dubbel — mag NIET opgeslagen worden
    {"bron": "pararius", "externe_id": "test001", "adres": "Ginnekenstraat 45", "prijs": 1200, "oppervlakte": 72, "kamers": 3, "link": "https://pararius.nl/test1", "gevonden_op": datetime.now().isoformat()},
]

resultaten = [sla_listing_op(l) for l in testdata]
print("Opgeslagen (True=nieuw, False=duplicaat):", resultaten)
print("Totaal in database:", tel_listings())
print()
listings = haal_listings_op(dagen=1)
for l in listings:
    print(f"  {l['adres']} - €{l['prijs']}/mnd - {l['bron']}")
