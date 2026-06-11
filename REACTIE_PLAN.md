# Plan: automatisch reageren op nieuwe woningen

> Onderzoek uitgevoerd op 11 juni 2026. Nog niet gebouwd — eerst moet de
> ochtendtest van 12 juni bewijzen dat de pipeline-planning 100% werkt.

## Waarom
Wie het eerst reageert op een huurwoning heeft de grootste kans. De pipeline
vindt woningen al automatisch; de reactie zelf is nu nog handwerk.

## Wat kan er per bron? (onderzocht in de echte alert-mails)

| Bron | Contactgegevens in mail | Automatisch reageren? |
|---|---|---|
| ikwilhuren.nu | ✅ e-mail makelaar (bijv. verhuur.wonen@mvgm.nl) + telefoon | **JA — direct per e-mail** |
| Rentumo | ❌ alleen doorverwijslink | Nee — wel snelle handmatige reactie |
| HuurwoningPortaal | ❌ alleen doorverwijslink | Nee — wel snelle handmatige reactie |
| Pararius | (geen recente mail om te checken) | Vermoedelijk alleen via hun formulier |
| Funda | (idem) | Alleen via funda-account |

**Harde grens (projectafspraak):** we scrapen niet en vullen geen formulieren
op andermans sites met een bot in (ToS, captcha's, juridisch risico). Automatisch
reageren doen we dus alleen waar een e-mailadres beschikbaar is.

## Twee modi (kunnen naast elkaar bestaan)

### Modus A — Volautomatisch (aanrader voor maximale snelheid)
De pipeline stuurt **direct bij ontdekking** een reactie-e-mail naar de makelaar,
in dezelfde run. Latentie: **0 extra seconden** na ontdekking.

- Werkt alleen voor woningen die aan de zoekcriteria voldoen
  (max €1200, min 50 m², min 1 aparte slaapkamer) — criteria-check moet nog
  in de pipeline gebouwd worden (staat er nu niet in!).
- Werkt alleen bij bronnen met bekend e-mailadres (nu: ikwilhuren.nu).
- Gebruiker keurt **eenmalig** de standaard-reactiebrief goed; daarna gaat
  het vanzelf. Telegram meldt achteraf: "✅ Al gereageerd op [adres] om 09:23".
- De brief kan per woning gepersonaliseerd worden met de Claude API
  (adres/kenmerken invullen; API-key zit al in de secrets).

**Belangrijk inzicht:** bij een akkoord-knop is de mens de bottleneck — als je
slaapt of op school zit, gaat de voorsprong verloren. Volautomatisch is daarom
objectief de snelste optie.

### Modus B — Akkoord-knop in Telegram
Voor wie per woning wil beslissen:

1. Telegram-bericht krijgt inline-knoppen: `✅ Reageer` / `⏭ Sla over`
   (Telegram Bot API: `reply_markup.inline_keyboard`, geverifieerd beschikbaar;
   er is geen webhook actief dus `getUpdates` werkt).
2. Een pg_cron-job in Supabase pollt **elke minuut** `getUpdates` via
   `net.http_get` (geverifieerd beschikbaar) en zet kliks in een tabel.
3. Bij een ✅-klik: `net.http_post` naar GitHub `workflow_dispatch` van een
   nieuw, klein workflow-bestand `reageer.yml` met de listing-id als input —
   exact dezelfde bewezen route als de pipeline-trigger (14/14 succes).
4. Die workflow zoekt de woning + makelaar-e-mail op in de database, stuurt
   de reactiebrief via Gmail SMTP (werkt al) en bevestigt in Telegram.

Latentie na klik: ±1 à 2,5 min (poll ≤60s + workflow-opstart). Totale snelheid
hangt af van hoe snel jij klikt.

### Bronnen zonder e-mailadres (Rentumo, HuurwoningPortaal, …)
Snelste legale optie: het Telegram-bericht bevat een **kant-en-klare
reactietekst** (kopieer-plak) + de directe link. Eén tik, plakken, versturen.

## Extra snelheidswinst los van reageren
De grootste vertraging zit in de **ontdekking**: de pipeline draait nu elke
30 min. De pg_cron-trigger kan gratis naar elke 10–15 min (GitHub Actions is
gratis voor publieke repos; de Claude API kost alleen iets bij écht nieuwe
woningen). Aanrader: 15 min.

## Wat er nog gebouwd moet worden (volgorde)
1. Criteria-filter in de pipeline (max prijs / min m² / slaapkamers) — nodig
   voor beide modi.
2. Reactieprofiel: standaardbrief + persoonsgegevens als GitHub-secret
   `REACTIE_PROFIEL` (niet hardcoded, conform projectafspraken).
3. Modus A: verstuurlogica in de pipeline + Telegram-bevestiging + logtabel
   `verstuurde_reacties` (nooit 2x op dezelfde woning reageren).
4. Modus B: inline-knoppen + Supabase-poller + `reageer.yml`.
5. Kopieer-plak-reactietekst in Telegram voor bronnen zonder e-mail.

## Openstaande keuzes voor de gebruiker
- Modus A, B of allebei?
- Inhoud van de standaard-reactiebrief (naam, situatie, inkomen vermelden?).
- Pipeline-frequentie naar 15 of 10 min?
