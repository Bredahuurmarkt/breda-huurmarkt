# Breda Huurmarkt Monitor — Projectgeheugen

> Dit bestand geeft toekomstige Claude Code sessies de context van dit project.
> Lees dit eerst voordat je iets bouwt.

## Wat bouwen we?
Een geautomatiseerd systeem dat de huurwoningmarkt in **Breda** dagelijks bijhoudt:
1. Verzamelt nieuwe huurwoningaanbiedingen
2. Genereert een AI-samenvatting (Claude API) van wat nieuw is
3. Houdt een live Streamlit-dashboard bij
4. Stuurt dagelijks een e-mailoverzicht

## Kernbeslissing: GEEN scraping
Funda en Pararius hebben databankrecht op hun listings — scrapen is juridisch riskant
en technisch lastig (captcha's). **Daarom lezen we de e-mailalerts** die de platforms
zelf versturen naar de Gmail-inbox van de gebruiker. Volledig legaal, geen captcha's.

**Constraint: nooit scrapen. Nergens. Alleen e-mail verwerken die naar ons gestuurd is.**

## Pipeline
```
Gmail API leest alert-mails
  -> Parser haalt listings eruit (adres, prijs, m2, kamers, link, bron, datum)
  -> Deduplicatie tegen database
  -> Nieuwe listings opslaan in SQLite
  -> Claude API genereert dagelijkse samenvatting
  -> Samenvatting versturen via e-mail
  -> Streamlit dashboard leest laatste stand uit database
```
De "24/7" zit in een scheduler (later: GitHub Actions), niet in een continu draaiende AI.

## Tech stack (al besloten — niet heroverwegen)
| Component | Technologie |
|---|---|
| Taal | Python 3.12 |
| Database | SQLite lokaal (-> Supabase later) |
| Dashboard | Streamlit |
| Gmail | Google Gmail API |
| AI | Anthropic Claude API |
| Notificatie | Gmail SMTP (-> Telegram later) |
| Hosting | Lokaal (fase 1) -> GitHub Actions (fase 2) |

## Bestandsstructuur
```
huurmarkt/
├── CLAUDE.md            # dit bestand
├── .env                 # secrets (NOOIT in git)
├── .env.example         # template
├── .gitignore
├── requirements.txt
├── data/huurmarkt.db    # SQLite database
├── src/
│   ├── gmail_reader.py  # Gmail API: alert-mails ophalen
│   ├── parser.py        # mails -> gestructureerde data
│   ├── database.py      # opslaan, ophalen, dedup
│   ├── ai_summary.py    # Claude API dagelijks overzicht
│   └── notifier.py      # e-mail versturen
├── dashboard.py         # Streamlit dashboard
└── run_pipeline.py      # koppelt alles aan elkaar
```

## MVP Fase 1 (huidige focus)
1. Gmail API verbinding (inbox lezen, filteren op afzender/label)
2. Parser voor Pararius alert-mail
3. SQLite opslag met dedup
4. Simpel Streamlit dashboard (tabel + prijs-over-tijd grafiek)
5. Dagelijkse Claude-samenvatting
6. Lokaal draaien op Windows

## Fase 2 (later, pas als fase 1 werkt)
Funda + Huurwoningen.nl, GitHub Actions + Supabase, Telegram bot, trendanalyse, kaart.

## Filters Breda
- Stad: Breda (alle wijken)
- Type: huurwoning (appartement of huis)
- Prijs: alle klassen (marktoverzicht)
- Specifieke filters later via .env/config

## Afspraken
- **Nooit scrapen.**
- Begin lokaal, niets in de cloud tot het lokaal werkt.
- Geen overengineering — werkende code, itereren.
- Leg uit wat je doet (gebruiker wil het begrijpen).
- Alle secrets in `.env`, nooit hardcoded.
- Schrijf in het Nederlands (behalve code/variabelen/comments).

## Status / voortgang
- [x] Python 3.12 geïnstalleerd
- [x] Projectstructuur aangemaakt
- [x] Config-bestanden (.env, requirements.txt, .gitignore)
- [x] Packages geïnstalleerd (venv: C:\Users\dasga\venvs\huurmarkt)
- [x] Gmail API verbinding (gmail_reader.py — token.json aanwezig)
- [x] Parser alle drie bronnen (parser.py — wacht op echte alert-mails voor fine-tuning)
- [x] Database + dedup (database.py — SQLite, UNIQUE constraint op bron+externe_id)
- [x] Dashboard (dashboard.py — Streamlit op http://localhost:8501)
- [x] AI-samenvatting (ai_summary.py — vereist ANTHROPIC_API_KEY in .env)
- [x] Notifier (notifier.py — vereist GMAIL_APP_PASSWORD in .env)
- [x] Pipeline (run_pipeline.py — python run_pipeline.py [--droog])

## Wat nu nog nodig is
1. **Pararius/Funda alerts instellen** (gebruiker): stel zoekopdrachten in op pararius.nl en funda.nl
   - Pararius: Zoeken → Breda → "Sla zoekopdracht op" → vink e-mailmelding aan
   - Funda: Account → Mijn zoekopdrachten → e-mailfrequentie instellen
2. **Anthropic API key** invullen in .env: ANTHROPIC_API_KEY=sk-ant-...
3. **Gmail App-wachtwoord** aanmaken voor SMTP (niet het gewone wachtwoord!):
   - Google Account → Beveiliging → 2FA aan → App-wachtwoorden → Maak aan
   - Vul in .env in: GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
4. **Parser fine-tunen** zodra de eerste echte alert-mails binnenkomen
