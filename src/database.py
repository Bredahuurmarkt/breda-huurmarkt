"""
Database module — werkt met zowel Supabase (PostgreSQL) als lokale SQLite.
Als DATABASE_URL in .env staat → Supabase. Anders → lokale SQLite.
"""
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud zet secrets in st.secrets — probeer dat eerst, dan .env
def _get_secret(key, default=""):
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

DATABASE_URL = _get_secret("DATABASE_URL", "")
DATABASE_PATH = Path(__file__).parent.parent / os.getenv("DATABASE_PATH", "data/huurmarkt.db")

USE_POSTGRES = bool(DATABASE_URL)


def _verbinding():
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        DATABASE_PATH.parent.mkdir(exist_ok=True)
        return sqlite3.connect(str(DATABASE_PATH))


def initialiseer_database():
    if USE_POSTGRES:
        _initialiseer_postgres()
    else:
        _initialiseer_sqlite()


def _initialiseer_postgres():
    import psycopg2
    conn = _verbinding()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id          SERIAL PRIMARY KEY,
                    bron        TEXT NOT NULL,
                    externe_id  TEXT,
                    adres       TEXT,
                    stad        TEXT DEFAULT 'Breda',
                    prijs       INTEGER,
                    oppervlakte INTEGER,
                    kamers      INTEGER,
                    link        TEXT,
                    gevonden_op TEXT NOT NULL,
                    actief      BOOLEAN DEFAULT TRUE,
                    UNIQUE(bron, externe_id)
                )
            """)
            # Voeg actief kolom toe als die nog niet bestaat (migratie)
            cur.execute("""
                ALTER TABLE listings ADD COLUMN IF NOT EXISTS actief BOOLEAN DEFAULT TRUE
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS samenvattingen (
                    id          SERIAL PRIMARY KEY,
                    datum       TEXT NOT NULL UNIQUE,
                    tekst       TEXT NOT NULL,
                    aangemaakt  TEXT NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()


def _initialiseer_sqlite():
    import sqlite3
    with _verbinding() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                bron        TEXT NOT NULL,
                externe_id  TEXT,
                adres       TEXT,
                stad        TEXT DEFAULT 'Breda',
                prijs       INTEGER,
                oppervlakte INTEGER,
                kamers      INTEGER,
                link        TEXT,
                gevonden_op TEXT NOT NULL,
                UNIQUE(bron, externe_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS samenvattingen (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                datum       TEXT NOT NULL UNIQUE,
                tekst       TEXT NOT NULL,
                aangemaakt  TEXT NOT NULL
            )
        """)
        conn.commit()


def sla_listing_op(listing: dict) -> bool:
    """Slaat een listing op. Geeft True terug als het nieuw was, False als duplicaat."""
    if USE_POSTGRES:
        return _sla_op_postgres(listing)
    else:
        return _sla_op_sqlite(listing)


def _sla_op_postgres(listing: dict) -> bool:
    import psycopg2
    conn = _verbinding()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO listings (bron, externe_id, adres, stad, prijs, oppervlakte, kamers, link, gevonden_op)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bron, externe_id) DO NOTHING
            """, (
                listing.get("bron", "onbekend"),
                listing.get("externe_id"),
                listing.get("adres"),
                listing.get("stad", "Breda"),
                listing.get("prijs"),
                listing.get("oppervlakte"),
                listing.get("kamers"),
                listing.get("link"),
                listing.get("gevonden_op", datetime.now().isoformat()),
            ))
            nieuw = cur.rowcount > 0
        conn.commit()
        return nieuw
    except Exception as e:
        conn.rollback()
        print(f"DB fout: {e}")
        return False
    finally:
        conn.close()


def _sla_op_sqlite(listing: dict) -> bool:
    import sqlite3
    try:
        with _verbinding() as conn:
            conn.execute("""
                INSERT INTO listings (bron, externe_id, adres, stad, prijs, oppervlakte, kamers, link, gevonden_op)
                VALUES (:bron, :externe_id, :adres, :stad, :prijs, :oppervlakte, :kamers, :link, :gevonden_op)
            """, {
                "bron": listing.get("bron", "onbekend"),
                "externe_id": listing.get("externe_id"),
                "adres": listing.get("adres"),
                "stad": listing.get("stad", "Breda"),
                "prijs": listing.get("prijs"),
                "oppervlakte": listing.get("oppervlakte"),
                "kamers": listing.get("kamers"),
                "link": listing.get("link"),
                "gevonden_op": listing.get("gevonden_op", datetime.now().isoformat()),
            })
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


def haal_listings_op(dagen=30, limit=500) -> list:
    """Haalt alleen actieve listings op — verlopen woningen worden automatisch uitgefilterd."""
    if USE_POSTGRES:
        conn = _verbinding()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, bron, externe_id, adres, stad, prijs, oppervlakte, kamers, link, gevonden_op
                    FROM listings
                    WHERE actief = TRUE
                    AND gevonden_op::timestamptz >= NOW() - (INTERVAL '1 day' * %s)
                    ORDER BY gevonden_op DESC
                    LIMIT %s
                """, (dagen, limit))
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()
    else:
        import sqlite3
        with _verbinding() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM listings
                WHERE actief = 1
                AND gevonden_op >= datetime('now', ?)
                ORDER BY gevonden_op DESC LIMIT ?
            """, (f"-{dagen} days", limit)).fetchall()
            return [dict(r) for r in rows]


def deactiveer_oude_listings(max_dagen=21):
    """Markeert woningen als inactief als ze ouder zijn dan max_dagen dagen."""
    if USE_POSTGRES:
        conn = _verbinding()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE listings SET actief = FALSE
                    WHERE actief = TRUE
                    AND gevonden_op::timestamptz < NOW() - (INTERVAL '1 day' * %s)
                """, (max_dagen,))
                aantal = cur.rowcount
            conn.commit()
            return aantal
        finally:
            conn.close()
    else:
        with _verbinding() as conn:
            cur = conn.execute("""
                UPDATE listings SET actief = 0
                WHERE actief = 1
                AND gevonden_op < datetime('now', ?)
            """, (f"-{max_dagen} days",))
            conn.commit()
            return cur.rowcount


def haal_nieuwe_listings_op(datum: str) -> list:
    if USE_POSTGRES:
        conn = _verbinding()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, bron, externe_id, adres, stad, prijs, oppervlakte, kamers, link, gevonden_op
                    FROM listings WHERE gevonden_op >= %s ORDER BY gevonden_op DESC
                """, (datum,))
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()
    else:
        import sqlite3
        with _verbinding() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM listings WHERE gevonden_op >= ? ORDER BY gevonden_op DESC
            """, (datum,)).fetchall()
            return [dict(r) for r in rows]


def sla_samenvatting_op(datum: str, tekst: str):
    if USE_POSTGRES:
        conn = _verbinding()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO samenvattingen (datum, tekst, aangemaakt)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (datum) DO UPDATE SET tekst = EXCLUDED.tekst
                """, (datum, tekst, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()
    else:
        with _verbinding() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO samenvattingen (datum, tekst, aangemaakt)
                VALUES (?, ?, ?)
            """, (datum, tekst, datetime.now().isoformat()))
            conn.commit()


def tel_listings() -> int:
    if USE_POSTGRES:
        conn = _verbinding()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM listings")
                return cur.fetchone()[0]
        finally:
            conn.close()
    else:
        with _verbinding() as conn:
            return conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]


if __name__ == "__main__":
    modus = "Supabase (PostgreSQL)" if USE_POSTGRES else "Lokale SQLite"
    print(f"Database modus: {modus}")
    initialiseer_database()
    print(f"Tabellen aangemaakt/gecontroleerd")
    print(f"Totaal listings: {tel_listings()}")
