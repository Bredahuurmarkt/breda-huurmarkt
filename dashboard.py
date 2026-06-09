import streamlit as st
import pandas as pd
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import initialiseer_database, haal_listings_op, tel_listings

st.set_page_config(
    page_title="Breda Huurmarkt",
    page_icon="🏠",
    layout="centered",  # beter voor mobiel
    initial_sidebar_state="collapsed",
)

# --- CSS voor mobiel-vriendelijk design ---
st.markdown("""
<style>
    /* Algemeen */
    .main > div { padding-top: 1rem; }

    /* Header */
    .header-box {
        background: linear-gradient(135deg, #1a365d, #2b6cb0);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        text-align: center;
    }
    .header-box h1 { margin: 0; font-size: 1.6rem; }
    .header-box p  { margin: 0.3rem 0 0; font-size: 0.85rem; opacity: 0.85; }

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
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .kpi-card .nummer {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2b6cb0;
        line-height: 1;
    }
    .kpi-card .label {
        font-size: 0.75rem;
        color: #718096;
        margin-top: 0.3rem;
    }

    /* Woning kaartjes */
    .woning-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .woning-card .adres {
        font-weight: 600;
        font-size: 1rem;
        color: #1a202c;
    }
    .woning-card .prijs {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2b6cb0;
    }
    .woning-card .details {
        font-size: 0.8rem;
        color: #718096;
        margin-top: 0.3rem;
    }
    .woning-card .bron-badge {
        display: inline-block;
        background: #ebf8ff;
        color: #2b6cb0;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 99px;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .woning-card a {
        text-decoration: none;
        color: inherit;
    }

    /* Filters */
    .filter-bar {
        background: #f7fafc;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
    }

    /* Sectie titels */
    .sectie-titel {
        font-size: 1rem;
        font-weight: 700;
        color: #2d3748;
        margin: 1rem 0 0.5rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #ebf8ff;
    }

    /* Streamlit elementen opschonen */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0.5rem 1rem 2rem; max-width: 680px; }
</style>
""", unsafe_allow_html=True)

initialiseer_database()

# --- Header ---
st.markdown(f"""
<div class="header-box">
    <h1>🏠 Breda Huurmarkt</h1>
    <p>Bijgewerkt op {date.today().strftime('%d %B %Y')}</p>
</div>
""", unsafe_allow_html=True)

# --- Filters (compact) ---
with st.expander("⚙️ Filters", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        dagen = st.slider("Laatste N dagen", 1, 90, 30)
        max_prijs = st.number_input("Max prijs (€)", 0, 5000, 1200, 50)
    with col2:
        min_opp = st.number_input("Min m²", 0, 200, 50, 5)
        bronnen = st.multiselect("Bron", ["pararius","funda","huurwoningen","rentumo","huizenvinder","huurportaal"],
                                 default=["pararius","funda","huurwoningen","rentumo","huizenvinder","huurportaal"])

# --- Data ophalen ---
listings = haal_listings_op(dagen=dagen)

if not listings:
    st.info("⏳ Nog geen woningen — de eerste alerts komen morgenochtend vroeg binnen!")
    st.stop()

df = pd.DataFrame(listings)
df["gevonden_op"] = pd.to_datetime(df["gevonden_op"])

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
        <div class="nummer">{tel_listings()}</div>
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

for _, row in df.iterrows():
    adres = row.get("adres") or "Adres onbekend"
    prijs = f"€{int(row['prijs'])}/mnd" if pd.notna(row.get("prijs")) else "Prijs onbekend"
    opp = f"{int(row['oppervlakte'])} m²" if pd.notna(row.get("oppervlakte")) else ""
    kamers = f"{int(row['kamers'])} kamers" if pd.notna(row.get("kamers")) else ""
    details = " · ".join(filter(None, [opp, kamers]))
    datum = row["gevonden_op"].strftime("%d-%m om %H:%M")
    link = row.get("link", "#")
    bron = row.get("bron", "").capitalize()

    st.markdown(f"""
    <div class="woning-card">
        <a href="{link}" target="_blank">
            <div class="adres">{adres}</div>
            <div class="prijs">{prijs}</div>
            <div class="details">{details + (' · ' if details else '') + datum}</div>
            <span class="bron-badge">{bron}</span>
        </a>
    </div>
    """, unsafe_allow_html=True)

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
