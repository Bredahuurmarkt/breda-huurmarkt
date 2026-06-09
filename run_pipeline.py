"""
Breda Huurmarkt Monitor — dagelijkse pipeline.

Gebruik:
    python run_pipeline.py            # normale run
    python run_pipeline.py --droog    # alles zonder e-mail en markeren
"""
import sys
import argparse
from datetime import date, timedelta

from src.database import initialiseer_database, haal_nieuwe_listings_op, tel_listings, sla_listing_op, deactiveer_oude_listings
from src.gmail_reader import haal_alert_mails_op, haal_mail_inhoud_op, markeer_als_gelezen
from src.parser import verwerk_mail


def main(droog: bool = False):
    print("=" * 50)
    print(f"Breda Huurmarkt Monitor — {date.today()}")
    print("=" * 50)

    # Stap 1: database gereedmaken
    initialiseer_database()
    print(f"Database: {tel_listings()} bestaande listings")

    # Verlopen woningen automatisch deactiveren (ouder dan 21 dagen)
    verlopen = deactiveer_oude_listings(max_dagen=21)
    if verlopen:
        print(f"  {verlopen} verlopen woning(en) gedeactiveerd (>21 dagen oud)")

    # Stap 2: alert-mails ophalen
    print("\n[1/4] Alert-mails ophalen uit Gmail...")
    mails = haal_alert_mails_op(max_results=50)
    print(f"  {len(mails)} ongelezen alert-mail(s) gevonden")

    if not mails:
        print("  Niets te verwerken. Klaar.")
        return

    # Stap 3: mails verwerken
    print("\n[2/4] Mails verwerken en listings opslaan...")
    nieuw_totaal = 0
    verwerkt_ids = []

    for mail_meta in mails:
        mail = haal_mail_inhoud_op(mail_meta["id"])
        listings = verwerk_mail(mail)
        print(f"  Mail van {mail['afzender'][:40]}: {len(listings)} listing(s) gevonden")

        for listing in listings:
            is_nieuw = sla_listing_op(listing)
            if is_nieuw:
                nieuw_totaal += 1

        verwerkt_ids.append(mail["id"])

    print(f"  {nieuw_totaal} nieuwe woning(en) toegevoegd aan database")

    if not droog:
        for mail_id in verwerkt_ids:
            markeer_als_gelezen(mail_id)
        print("  Mails gemarkeerd als gelezen")

    # Stap 4: AI-samenvatting (alleen als er nieuwe listings zijn)
    print("\n[3/4] AI-samenvatting genereren...")
    vandaag_start = date.today().isoformat() + "T00:00:00"
    nieuwe_listings = haal_nieuwe_listings_op(vandaag_start)

    if not nieuwe_listings:
        print("  Geen nieuwe listings vandaag — samenvatting overgeslagen")
        samenvatting = "Vandaag zijn er geen nieuwe huurwoningen gevonden in Breda."
    else:
        try:
            from src.ai_summary import genereer_dagelijkse_samenvatting
            samenvatting = genereer_dagelijkse_samenvatting(vandaag_start)
            print(f"  Samenvatting gegenereerd ({len(samenvatting)} tekens)")
        except Exception as e:
            samenvatting = f"Samenvatting kon niet worden gegenereerd ({e})."
            print(f"  Fout bij AI-samenvatting: {e}")

    print(f"\n  {samenvatting[:200]}{'...' if len(samenvatting) > 200 else ''}")

    # Stap 5: e-mail versturen
    print("\n[4/4] Dagelijks overzicht e-mailen...")
    if droog:
        print("  --droog modus: e-mail overgeslagen")
    else:
        try:
            from src.notifier import stuur_dagelijks_overzicht
            stuur_dagelijks_overzicht(samenvatting, nieuwe_listings)
        except Exception as e:
            print(f"  E-mail mislukt: {e}")

    print("\n✓ Pipeline klaar")
    print(f"  Database bevat nu {tel_listings()} listings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Breda Huurmarkt Monitor pipeline")
    parser.add_argument("--droog", action="store_true", help="Geen e-mail, geen mails markeren")
    args = parser.parse_args()
    main(droog=args.droog)
