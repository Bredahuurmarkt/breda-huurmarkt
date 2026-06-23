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
Gmail API leest alert-mails (newer_than:1d, NIET is:unread — telefoonmeldingen
                             markeren mails als gelezen vóór de pipeline draait)
  -> Parser haalt listings eruit (adres, prijs, m2, kamers, foto, link, bron, datum)
  -> Deduplicatie tegen database (UNIQUE op bron+externe_id)
  -> Nieuwe listings opslaan in Supabase (PostgreSQL)
  -> Claude API genereert samenvatting (alleen bij echt nieuwe woningen)
  -> E-mail (woningkaarten met foto) + Telegram (sendPhoto per woning)
  -> Streamlit dashboard (breda-huurmarkt.streamlit.app) leest live uit Supabase
```

## Planning (belangrijk!)
**GitHub's eigen cron vuurt NOOIT voor deze repo** (bewezen: 0 van de 27+ tikken,
ook na disable/enable-reset). De echte planner is **Supabase pg_cron**:
- Job `huurmarkt-pipeline-trigger`, schedule `20,50 7-15 * * *` (UTC)
- Roept via pg_net de GitHub workflow_dispatch API aan (PAT in de job-SQL)
- Beheren: `SELECT * FROM cron.job;` / logs: `SELECT * FROM cron.job_run_details;`
- De GitHub-schedule (`5,35 7-15 * * *`) blijft als gratis backup staan
- Ochtendcheck-Telegram max 1x/dag via `claim_ochtendcheck()` (systeem_status-tabel)

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

## Status / voortgang (per 11 juni 2026)
- [x] Volledige pipeline draait in de cloud (GitHub Actions, getriggerd door Supabase pg_cron)
- [x] Database: Supabase PostgreSQL (DATABASE_URL in .env; lokale SQLite is fallback)
- [x] Dashboard live op breda-huurmarkt.streamlit.app (met "Nu mail checken"-knop)
- [x] Bronnen met eigen parser: pararius, funda, huurwoningen, google alerts,
      rentumo (eigen parser: slug-dedup, "Vergelijkbare aanbiedingen" genegeerd),
      ikwilhuren, huurwoningportaal (Mailjet-links gedecodeerd), huizenvinder (generiek)
- [x] Notificaties: e-mail (woningkaarten met foto) + Telegram-bot @HuurMarktBreda_bot
      (foto per woning) + dagelijkse ochtendcheck (max 1x/dag, claim in systeem_status)
- [x] Zoekcriteria gebruiker: max €1200/mnd, min 50 m², min 1 aparte slaapkamer

## Geleerde lessen (niet opnieuw tegenaan lopen)
- GitHub Actions cron werkt niet voor deze repo → planning via Supabase pg_cron
- Gmail `is:unread` filter is onbetrouwbaar (telefoonmeldingen lezen mails) → `newer_than:1d`
- Rentumo: Mailchimp-trackinglinks variëren per voorkomen → dedup op advertentie-slug;
  watermerk-afbeelding (img_sign, base64 in proxy-URL) is geen woningfoto
- HuurwoningPortaal: links zijn Mailjet (mjt.lu), laatste padsegment = base64url doel-URL
- `--droog` slaat WEL op in de database (alleen mail/Telegram/markeren overgeslagen)
- GitHub-secrets zetten kan via API met PyNaCl SealedBox (venv heeft pynacl)
- **Gmail-token verloopt elke 7 dagen** zolang de OAuth-app in "Testing"-modus staat
  (fout: `invalid_grant: Token has been expired or revoked`, hele pipeline crasht).
  Permanente fix: app publiceren naar Productie (Google Cloud Console → OAuth consent
  screen → Publish App). Tijdelijke fix: lokaal opnieuw inloggen (InstalledAppFlow.
  run_local_server) → nieuwe token.json → base64 → GitHub-secret GMAIL_TOKEN_JSON.
- **iCloud Drive corrumpeert deze repo** door bewerkte bestanden te dupliceren naar
  "naam 2.ext" (ook binnen .git: `index 2`, `refs/heads/main 2`). Symptomen: bestanden
  ineens untracked, `bad object refs/heads/main 2`, of een bestand dat als verwijdering
  in een commit belandt. Herstel: backup .env/token.json/credentials.json, verse
  `git clone` buiten iCloud, `.git` omwisselen, `git reset --hard origin/main`,
  gitignore-bestanden terugzetten. Check vóór elke commit `git status` op "… 2"-bestanden.
- Dashboard heeft `tzdata` in requirements nodig (Streamlit Cloud mist IANA-tijdzones);
  pandas NaN-velden nooit met `x or ""` afhandelen (NaN is truthy) → eigen `_tekst()`-helper.
