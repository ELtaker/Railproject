# Raildrops Onboarding

Velkommen til Raildrops-prosjektet! Her finner du alt du trenger for å komme i gang som utvikler.

## 1. Kom i gang

1. **Klon repoet:**
   ```sh
   git clone <repo-url>
   cd Raildrops
   ```
2. **Opprett og aktiver virtuelt miljø:**
   ```sh
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Mac/Linux
   ```
3. **Installer avhengigheter:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Kopier .env-fil:**
   ```sh
   cp .env.example .env
   ```
   Fyll inn nødvendige variabler i `.env`.

## 2. Kjør utviklingsserver

```sh
python manage.py migrate
python manage.py runserver
```

## 3. Kjør tester

```sh
$env:DJANGO_SETTINGS_MODULE="config.settings"; pytest --maxfail=3 --disable-warnings -v
```

## 4. Kodekvalitet
- Følg PEP8 og prosjektets egne regler (se README).
- Kjør `flake8` og `stylelint` før commit.
- Skriv meningsfulle kommentarer og docstrings.
- Bruk logging, ikke print.

## 5. Brukerroller og medlemskap
- Raildrops bruker **Django Groups** for å håndtere brukerroller og medlemskap.
- Vanlige brukere legges i gruppen `Members` automatisk ved registrering.
- Bedriftsbrukere får en `business_profile` og er ikke i `Members`-gruppen.
- For å sjekke medlemskap, bruk alltid:
  ```python
  user.groups.filter(name="Members").exists() and not hasattr(user, "business_profile")
  ```
- For bedriftsbruker:
  ```python
  hasattr(user, "business_profile")
  ```
- Utvid roller ved å legge til nye grupper i Django admin og bruk gruppesjekk i permissions.py.
- All rollelogikk skal sentraliseres i `accounts/permissions.py` og/eller `giveaways/permissions.py`.

## 5. CI/CD
- Alle commits og pull requests kjøres gjennom GitHub Actions (se `.github/workflows/ci.yml`).
- Testene må passere før merge.

## 6. Prosjektstruktur
- **accounts/**: Brukerhåndtering, skjemaer, views, templates, tester
- **giveaways/**: Giveaways-funksjonalitet
- **businesses/**: Bedriftsrelatert funksjonalitet
- **notifications/**: Varslingssystem
- **config/**: Django settings og prosjektkonfig
- **static/**: CSS, JS, bilder
- **templates/**: Globale maler
- **utils/**: Gjenbrukbare funksjoner og logging

## 7. Viktige regler (utdrag)
- All validering i skjemaers `clean()` eller `clean_<field>()`.
- Bruk `ModelForm` for create/update.
- Logging skal brukes for alle viktige hendelser og feil.
- Ingen forretningslogikk i `config/`.
- Universell utforming (a11y) og Bootstrap 5 i alle templates.
- Ingen hemmeligheter i kode eller git.

Se README for fullstendig regelsett og mer informasjon.

---

**Spørsmål?**
Kontakt tech lead eller se README for mer info.
