# Raildrops

## Prosjektstruktur
- accounts/         # Brukere og autentisering
- businesses/       # Bedriftsprofiler
- giveaways/        # Giveaways og påmeldinger
- notifications/    # Varslinger
- templates/        # HTML-maler
- static/           # CSS, JS, bilder
- utils/            # Fellesfunksjoner (logging, etc.)

## Regler og konvensjoner
- Se `.windsurfrules` for alle koderegler og strukturkrav.
- All forretningslogikk skal ligge i `services.py`.
- Alle forms skal bruke ModelForm og validering i clean().
- Alle sensitive verdier skal ligge i `.env`.

### Brukerroller og medlemskap
- Raildrops bruker **Django Groups** for å håndtere roller og medlemskap.
- Vanlige brukere legges automatisk i gruppen `Members` ved registrering.
- Bedriftsbrukere får en tilknyttet `business_profile` og er ikke i `Members`-gruppen.
- For å sjekke medlemskap, bruk alltid:
  ```python
  user.groups.filter(name="Members").exists() and not hasattr(user, "business_profile")
  ```
- For bedriftsbruker:
  ```python
  hasattr(user, "business_profile")
  ```
- Utvid roller ved å legge til nye grupper i Django admin og bruke gruppesjekk i permissions.py.
- All rollelogikk skal sentraliseres i `accounts/permissions.py` og/eller `giveaways/permissions.py`.

## Utviklingsprosess og status

Dette prosjektet gir en komplett, offentlig giveaways-funksjon for Raildrops-plattformen. Prosessen har fulgt moderne Django-praksis, med fokus på modulær kode, universell utforming og god dokumentasjon.

### 1. Oppstart og struktur
- Prosjektet satt opp som et Django-prosjekt med separate apper for `giveaways`, `businesses`, `accounts` m.m.
- Kodebase strukturert etter Windsurf-reglene for modulær Django-utvikling.
- Bruk av pre-commit hooks, .env-filer og requirements.txt for miljøkontroll.

### 2. Modellering og database
- Modell for Giveaway med felter for premie, verdi, start/sluttdato, spørsmål, svaralternativer, kobling til bedrift og aktiv-status.
- Modell for Entry (påmelding) og kobling til bruker.
- Relasjoner mellom giveaways og bedrifter.

### 3. Offentlig oversikt og filtrering
- Implementert horisontal scroll med giveaways-kort, filtrerbare på lokasjon (by, postnummer).
- Kortene viser bedriftsnavn, logo, premie, verdi, sted og antall deltakere.
- Bruk av Bootstrap 5 og moderne CSS3 for responsiv og universelt utformet visning.

### 4. Detaljvisning og påmelding
- Detaljside for hver giveaway med all info og påmeldingsskjema.
- Skjemaet viser spørsmål og svaralternativer (radio), og håndterer status for påmelding.
- Dynamisk visning av påmeldingsmulighet basert på om bruker er innlogget/allerede påmeldt.

---

## Formation & History

Raildrops-prosjektet ble startet våren 2025 med mål om å lage en moderne, universelt utformet plattform for giveaways og konkurranser mellom bedrifter og medlemmer. Prosjektet bygger på følgende utviklingsfaser og milepæler:

- **Oppstart og planlegging:**
  - Prosjektet ble initiert med fokus på sikkerhet, universell utforming, og et solid teknisk grunnlag.
  - Valg av Django som backend-rammeverk og Bootstrap 5 for frontend.
  - Strenge arkitekturregler (se Windsurf-regler) ble etablert for å sikre modulær, testbar kode og god dokumentasjon.

- **Første utviklingsfase:**
  - Oppsett av prosjektstruktur, apps for `accounts` (brukere/bedrifter) og `businesses`.
  - Implementering av Company (custom user model) og Business-modell med admin-felt.
  - Registreringsflyt for både medlemmer og bedrifter, med automatisk kobling av admin til bedrift.
  - Opprettelse av dashboard for bedriftsbrukere med relevante handlinger.

- **Videreutvikling:**
  - Implementering av giveaways, påmeldingssystem og dynamisk visning for ulike brukertyper.
  - Robust validering i forms (ModelForm og clean-metoder).
  - Kontinuerlig forbedring av brukeropplevelse og tilgjengelighet (a11y).
  - Løpende bugfixes, spesielt rundt kobling mellom Company og Business/admin-felt.
  - Tilbakemeldinger fra brukere og testere har ført til flere iterasjoner på påmeldingsflyt og dashboard.

- **Teknisk og organisatorisk:**
  - Alle endringer dokumenteres fortløpende i README og onboarding.md.
  - Prosjektet følger CI/CD-prinsipper, pre-commit hooks og har full testdekning for alle apps.
  - Miljøvariabler håndteres sikkert, og det finnes alltid en oppdatert `.env.example`.

---

### 5. Testing og frontend
- Frontend testet lokalt med Django runserver.
- Testside (`testpage.html`) viser alle giveaways horisontalt.

### 6. Neste steg
- Fullføre backend for påmelding (lagre Entry ved innsending).
- Flere tester og tilbakemeldinger fra brukere.

## Kom i gang
1. Klon repoet og lag `.env`-fil etter `.env.example`.
2. Opprett og aktiver virtuelt miljø:  
   `python -m venv .venv && source .venv/bin/activate` (Linux/Mac)  
   `.venv\Scripts\activate` (Windows)
3. Installer avhengigheter:  
   `pip install -r requirements.txt`
4. Kjør migrasjoner:  
   `python manage.py migrate`
5. Start server:  
   `python manage.py runserver`
6. Åpne i browser:  
   `http://127.0.0.1:8000`

## Arkitektur og prinsipper
- Django 5.2, Bootstrap 5, CSS3
- Streng modulær struktur (se Windsurf-regler)
- Universell utforming og tilgjengelighet (a11y)
- Alle forms via ModelForm og validering i clean-metoder
- Logging og docstrings på alle views

## Kontakt og bidrag
- Se onboarding.md for detaljer om prosjektregler og onboarding.
- Bidrag ønskes! Følg prosjektets kodestandard og send gjerne pull requests.
