"""
Breda Huurmarkt Monitor — dagelijkse pipeline.

Gebruik:
    python run_pipeline.py            # normale run
    python run_pipeline.py --droog    # alles zonder e-mail en markeren
"""
import argparse
from datetime import date

from src.database import initialiseer_database, tel_listings, sla_listing_op, deactiveer_oude_listings
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
    nieuwe_listings = []
    verwerkt_ids = []

    for mail_meta in mails:
        mail = haal_mail_inhoud_op(mail_meta["id"])
        listings = verwerk_mail(mail)
        print(f"  Mail van {mail['afzender'][:40]}: {len(listings)} listing(s) gevonden")

        for listing in listings:
            if sla_listing_op(listing):
                nieuwe_listings.append(listing)

        verwerkt_ids.append(mail["id"])

    print(f"  {len(nieuwe_listings)} nieuwe woning(en) toegevoegd aan database")

    if not droog:
        for mail_id in verwerkt_ids:
            markeer_als_gelezen(mail_id)
        print("  Mails gemarkeerd als gelezen")

    if not nieuwe_listings:
        print("\n[3/4] Geen nieuwe woningen — samenvatting en e-mail overgeslagen")
        print("\n✓ Pipeline klaar")
        print(f"  Database bevat nu {tel_listings()} listings")
        return

    # Stap 4: AI-samenvatting van de nieuwe listings
    print("\n[3/4] AI-samenvatting genereren...")
    try:
        from src.ai_summary import genereer_samenvatting
        samenvatting = genereer_samenvatting(nieuwe_listings)
        print(f"  Samenvatting gegenereerd ({len(samenvatting)} tekens)")
    except Exception as e:
        samenvatting = f"Er zijn {len(nieuwe_listings)} nieuwe woning(en) gevonden."
        print(f"  Fout bij AI-samenvatting: {e}")

    print(f"\n  {samenvatting[:200]}{'...' if len(samenvatting) > 200 else ''}")

    # Stap 5: e-mail en Telegram versturen
    print("\n[4/4] Overzicht versturen...")
    if droog:
        print("  --droog modus: e-mail en Telegram overgeslagen")
    else:
        try:
            from src.notifier import stuur_dagelijks_overzicht
            stuur_dagelijks_overzicht(samenvatting, nieuwe_listings)
        except Exception as e:
            print(f"  E-mail mislukt: {e}")

        try:
            from src.telegram_notify import stuur_nieuwe_woningen_telegram
            stuur_nieuwe_woningen_telegram(nieuwe_listings)
        except Exception as e:
            print(f"  Telegram mislukt: {e}")

    print("\n✓ Pipeline klaar")
    print(f"  Database bevat nu {tel_listings()} listings")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Breda Huurmarkt Monitor pipeline")
    parser.add_argument("--droog", action="store_true", help="Geen e-mail, geen mails markeren")
    args = parser.parse_args()
    main(droog=args.droog)
