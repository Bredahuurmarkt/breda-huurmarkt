import streamlit as st
import pandas as pd
import requests
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import initialiseer_database, haal_listings_op, _get_secret

GITHUB_TOKEN = _get_secret("GITHUB_TOKEN", "")
GITHUB_REPO = "Bredahuurmarkt/breda-huurmarkt"
GITHUB_WORKFLOW = "dagelijkse_pipeline.yml"

st.set_page_config(
    page_title="Breda Huurmarkt",
    page_icon="🏠",
    layout="centered",  # beter voor mobiel
    initial_sidebar_state="collapsed",
)


# --- Caching: database-werk maar 1x per sessie / per 2 minuten ---
@st.cache_resource
def _eenmalige_db_init():
    """DDL hoeft maar één keer per serverproces, niet bij elke page-load."""
    initialiseer_database()
    return True


@st.cache_data(ttl=120, show_spinner=False)
def _haal_listings_gecached(dagen: int):
    return haal_listings_op(dagen=dagen)


# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main > div { padding-top: 1rem; }

    /* Header */
    .header-box {
        background: linear-gradient(135deg, #0f2647 0%, #1d4ed8 60%, #3b82f6 100%);
        color: white;
        padding: 1.6rem 1.5rem 1.4rem;
        border-radius: 20px;
        margin-bottom: 1rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(29, 78, 216, 0.35);
    }
    .header-box h1 { margin: 0; font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; }
    .header-box p  { margin: 0.35rem 0 0; font-size: 0.85rem; opacity: 0.8; }

    /* KPI kaartjes */
    .kpi-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem 0.75rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(15, 38, 71, 0.06);
    }
    .kpi-card .nummer {
        font-size: 1.9rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1d4ed8, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }
    .kpi-card .label {
        font-size: 0.72rem;
        color: #64748b;
        margin-top: 0.25rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Woning kaartjes */
    .woning-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        overflow: hidden;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(15, 38, 71, 0.07);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .woning-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(15, 38, 71, 0.14);
    }
    .woning-card .foto {
        width: 100%;
        height: 190px;
        object-fit: cover;
        display: block;
    }
    .woning-card .foto-fallback {
        width: 100%;
        height: 110px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.4rem;
        background: linear-gradient(135deg, #e0eaff 0%, #f0f6ff 100%);
    }
    .woning-card .inhoud { padding: 0.9rem 1.1rem 1rem; }
    .woning-card .topregel {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.5rem;
    }
    .woning-card .adres {
        font-weight: 700;
        font-size: 1.02rem;
        color: #0f172a;
        letter-spacing: -0.01em;
    }
    .woning-card .prijs {
        font-size: 1.05rem;
        font-weight: 800;
        color: #1d4ed8;
        white-space: nowrap;
    }
    .woning-card .details {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.3rem;
    }
    .woning-card .badge-rij { margin-top: 0.55rem; display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .bron-badge {
        display: inline-block;
        background: #eff6ff;
        color: #1d4ed8;
        font-size: 0.68rem;
        padding: 3px 10px;
        border-radius: 99px;
        font-weight: 700;
    }
    .nieuw-badge {
        display: inline-block;
        background: #dcfce7;
        color: #15803d;
        font-size: 0.68rem;
        padding: 3px 10px;
        border-radius: 99px;
        font-weight: 700;
    }
    .woning-card a { text-decoration: none; color: inherit; }

    /* Sectie titels */
    .sectie-titel {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0f172a;
        margin: 1.2rem 0 0.6rem;
        letter-spacing: -0.01em;
    }

    /* Streamlit elementen opschonen */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0.5rem 1rem 2rem; max-width: 680px; }
    .stButton button {
        border-radius: 12px;
        font-weight: 700;
        border: none;
        background: linear-gradient(135deg, #1d4ed8, #3b82f6);
        color: white;
        padding: 0.6rem 1rem;
    }
    .stButton button:hover { filter: brightness(1.08); color: white; }
</style>
""", unsafe_allow_html=True)

_eenmalige_db_init()

# --- Header ---
st.markdown(f"""
<div class="header-box">
    <h1>🏠 Breda Huurmarkt</h1>
    <p>Live overzicht · bijgewerkt {date.today().strftime('%d %B %Y')}</p>
</div>
""", unsafe_allow_html=True)

# --- Handmatig mail ophalen ---
if st.button("📬 Nu mail checken", use_container_width=True):
    if not GITHUB_TOKEN:
        st.error("GITHUB_TOKEN ontbreekt in de secrets — kan de pipeline niet starten.")
    else:
        resp = requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/dispatches",
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={"ref": "main"},
        )
        if resp.status_code == 204:
            _haal_listings_gecached.clear()  # na de run verse data tonen
            st.success("Pipeline gestart! Dit duurt ongeveer 30-60 seconden — ververs deze pagina daarna voor nieuwe woningen.")
        else:
            st.error(f"Kon de pipeline niet starten ({resp.status_code}): {resp.text}")

# --- Data eerst ophalen (zodat filters de echte bronnen kennen) ---
dagen_default = 30
listings = _haal_listings_gecached(90)  # ruim ophalen, daarna filteren in UI

if not listings:
    st.info("⏳ Nog geen woningen — de eerste alerts komen vanzelf binnen via je e-mailalerts!")
    st.stop()

df_alle = pd.DataFrame(listings)
# Datums tijdzone-veilig maken: alles naar UTC, dan naar NL-tijd, dan tz weghalen.
# tz_convert("Europe/Amsterdam") heeft de IANA-tijdzonedatabase nodig (tzdata).
# Mocht die op de server ooit ontbreken, dan vallen we terug op kale UTC i.p.v.
# de hele pagina te laten crashen.
_utc = pd.to_datetime(df_alle["gevonden_op"], utc=True, errors="coerce")
try:
    df_alle["gevonden_op"] = _utc.dt.tz_convert("Europe/Amsterdam").dt.tz_localize(None)
except Exception:
    df_alle["gevonden_op"] = _utc.dt.tz_localize(None)
beschikbare_bronnen = sorted(df_alle["bron"].dropna().unique().tolist())

# --- Filters (compact) ---
with st.expander("⚙️ Filters", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        dagen = st.slider("Laatste N dagen", 1, 90, dagen_default)
        max_prijs = st.number_input("Max prijs (€)", 0, 5000, 1200, 50)
    with col2:
        min_opp = st.number_input("Min m²", 0, 200, 50, 5)
        # Standaard: ALLE bronnen die in de data zitten aangevinkt
        bronnen = st.multiselect("Bron", beschikbare_bronnen, default=beschikbare_bronnen)

# Tijdsfilter toepassen op basis van de slider
grens = pd.Timestamp.now() - pd.Timedelta(days=dagen)
df = df_alle[df_alle["gevonden_op"] >= grens].copy()

# Filters toepassen
if max_prijs > 0:
    df = df[df["prijs"].isna() | (df["prijs"] <= max_prijs)]
if min_opp > 0:
    df = df[df["oppervlakte"].isna() | (df["oppervlakte"] >= min_opp)]
if bronnen:
    df = df[df["bron"].isin(bronnen)]

df = df.sort_values("gevonden_op", ascending=False)

# --- KPI kaartjes ---
nieuw_vandaag = df[df["gevonden_op"].dt.date == date.today()]
gem_prijs = int(df["prijs"].mean()) if df["prijs"].notna().any() else 0
gem_prijs_str = f"€{gem_prijs:,}".replace(",", ".") if gem_prijs else "—"

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="nummer">{len(df_alle)}</div>
        <div class="label">Totaal gevonden</div>
    </div>
    <div class="kpi-card">
        <div class="nummer">{len(nieuw_vandaag)}</div>
        <div class="label">Nieuw vandaag</div>
    </div>
    <div class="kpi-card">
        <div class="nummer">{len(df)}</div>
        <div class="label">Afgelopen {dagen} dagen</div>
    </div>
    <div class="kpi-card">
        <div class="nummer">{gem_prijs_str}</div>
        <div class="label">Gemiddelde prijs</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Woning kaartjes ---
st.markdown('<div class="sectie-titel">🏡 Woningaanbod</div>', unsafe_allow_html=True)

def _tekst(row, key):
    """Veilige tekst uit een DataFrame-rij: lege string voor None én voor pandas NaN.
    (let op: 'NaN or \"\"' geeft in Python NaN terug, niet \"\" — vandaar deze helper.)"""
    val = row.get(key)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val)


for _, row in df.iterrows():
    adres   = _tekst(row, "adres") or "Adres onbekend"
    wijk    = _tekst(row, "wijk")
    prijs   = f"€{int(row['prijs'])}/mnd" if pd.notna(row.get("prijs")) else "Prijs onbekend"
    opp     = f"{int(row['oppervlakte'])} m²" if pd.notna(row.get("oppervlakte")) else ""
    kamers  = f"{int(row['kamers'])} kamer(s)" if pd.notna(row.get("kamers")) else ""
    bouwjaar = f"Bouwjaar {int(row['bouwjaar'])}" if pd.notna(row.get("bouwjaar")) else ""
    details = " · ".join(filter(None, [opp, kamers, bouwjaar]))
    datum   = row["gevonden_op"].strftime("%d-%m om %H:%M")
    link    = _tekst(row, "link") or "#"
    bron    = _tekst(row, "bron").capitalize()
    foto    = _tekst(row, "foto_url")
    is_nieuw = row["gevonden_op"].date() == date.today()
    makelaar      = _tekst(row, "makelaar")
    makelaar_tel  = _tekst(row, "makelaar_tel")
    makelaar_link = _tekst(row, "makelaar_link")

    # Foto met nette fallback
    if foto:
        foto_html = f'<img class="foto" src="{foto}" alt="{adres}">'
    else:
        foto_html = '<div class="foto-fallback">🏠</div>'

    locatie = f"📍 {wijk}, Breda" if wijk else "📍 Breda"

    # Badges
    badges = f'<span class="bron-badge">{bron}</span>'
    if is_nieuw:
        badges += '<span class="nieuw-badge">✨ Nieuw vandaag</span>'

    # Contact
    if makelaar_tel:
        contact_html = f'<a href="tel:{makelaar_tel}" style="display:inline-block; margin-top:0.6rem; background:#1d4ed8; color:white; padding:7px 16px; border-radius:10px; font-size:0.8rem; font-weight:700; text-decoration:none;">📞 {makelaar or "Bel makelaar"}</a>'
    elif makelaar_link:
        contact_html = f'<a href="{makelaar_link}" target="_blank" style="display:inline-block; margin-top:0.6rem; background:#1d4ed8; color:white; padding:7px 16px; border-radius:10px; font-size:0.8rem; font-weight:700; text-decoration:none;">✉️ {makelaar or "Contact makelaar"}</a>'
    elif makelaar:
        contact_html = f'<div class="details" style="margin-top:0.4rem;">🏢 {makelaar}</div>'
    else:
        contact_html = ""

    kaart_html = (
        '<div class="woning-card">'
        f'<a href="{link}" target="_blank">'
        f'{foto_html}'
        '<div class="inhoud">'
        '<div class="topregel">'
        f'<span class="adres">{adres}</span>'
        f'<span class="prijs">{prijs}</span>'
        '</div>'
        f'<div class="details">{locatie}</div>'
        f'<div class="details">{details}</div>'
        f'<div class="details" style="color:#94a3b8; font-size:0.72rem;">Gevonden op {datum}</div>'
        f'<div class="badge-rij">{badges}</div>'
        f'{contact_html}'
        '</div>'
        '</a>'
        '</div>'
    )
    st.markdown(kaart_html, unsafe_allow_html=True)

# --- Grafiek ---
st.markdown('<div class="sectie-titel">📈 Prijsontwikkeling</div>', unsafe_allow_html=True)
prijs_df = df[df["prijs"].notna()].copy()
if not prijs_df.empty:
    prijs_df["dag"] = prijs_df["gevonden_op"].dt.date
    gemiddeld = prijs_df.groupby("dag")["prijs"].mean().reset_index()
    gemiddeld.columns = ["dag", "Gem. prijs (€/mnd)"]
    st.line_chart(gemiddeld.set_index("dag"), height=200)
else:
    st.caption("Nog geen prijsdata beschikbaar.")
