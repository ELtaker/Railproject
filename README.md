# Raildrops - Django Web Application

Raildrops is a modular Django web application for managing location-based giveaways, supporting both individual members and business users. The project emphasizes clear separation of concerns, robust role-based permissions, and a modern, responsive user experience.

## Features

- **User Accounts:** Registration and authentication for both members and businesses.
- **Business Dashboard:** Businesses can create, manage, and view their giveaways.
- **Giveaways:** Location-based giveaways with participation logic, question/answer validation, and winner selection.
- **Notifications:** Centralized notification system for user and business activities.
- **Role-based Permissions:** Strict separation between member and business functionality.
- **Location Handling:** Businesses register their location; members can filter/join giveaways by location.
- **Testing:** Comprehensive unit and integration tests for all major apps.

## Application Structure

```
raildrops/
├── config/                # Django project configuration (settings, urls, wsgi, asgi)
├── accounts/              # User management (members and businesses), authentication, profiles
├── businesses/            # Business profile management, dashboard, business-specific tools
├── giveaways/             # Giveaway models, participation, winner logic
├── notifications/         # Notification system for users and businesses
├── templates/             # HTML templates, organized by app
├── static/                # Static files (CSS, JS, images)
├── tests/                 # Test directories for each app
├── utils/                 # Utility modules and helpers
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
└── ...
```

## User Roles & Models

- **Members:** Regular users who can join giveaways. Managed via Django Groups.
- **Businesses:** Users with a linked BusinessProfile. Can create and manage giveaways.
- **BusinessProfile:** Stores business info, location, and links to User.
- **Giveaway:** Represents a giveaway event, including title, description, location, question, answer options, and correct answer.
- **Participation:** Tracks member entries, selected answers, and timestamps. Ensures unique participation per giveaway.

## Giveaway Participation & Winner Selection

- Members can join active giveaways by answering a question.
- Only one entry per member per giveaway is allowed.
- Winner selection prioritizes correct answers and selects randomly among correct entries.
- Winner announcement and notification are handled via the notifications system.

## Permissions & Access Control

- Role-based permissions enforced via Django Groups and custom mixins.
- Only business users can access business dashboard and create giveaways.
- Members can view and join giveaways, but not create them.

## Location Features

- Businesses register their location during signup/profile management.
- Members may be prompted for location to filter available giveaways.
- Giveaways can be filtered and displayed based on user or business location.

## Setup & Installation

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd raildrops
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Apply migrations:**
   ```sh
   python manage.py migrate
   ```
5. **Create a superuser (admin):**
   ```sh
   python manage.py createsuperuser
   ```
6. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

## Running Tests

To run all tests:
```sh
python manage.py test
```
Each app has its own `tests/` directory with unit and integration tests.

## Contributing
- Follow PEP8 and Django best practices.
- Write meaningful comments and docstrings.
- Add/maintain tests for all features.
- Keep code modular and well-documented.

## License
This project is licensed under the MIT License.

---

For more details, see the code and inline documentation. For onboarding and developer notes, see `ONBOARDING.md`.
    # Skjemaer relatert til brukerregistrering, innlogging og profilhåndtering
│   ├── managers.py                 # Egendefinerte modell-managere for accounts-modellene
│   ├── migrations/                 # Inneholder database-migrasjoner for 'accounts'-appen
│   │   └── ...                     # (f.eks., __init__.py og migrasjonsfiler)
│   ├── models.py                   # Definisjoner for datamodellene knyttet til brukere og bedriftsprofiler
│   ├── permissions.py              # Definerer tilgangskontroller og rettigheter for 'accounts'-appen
│   ├── templates/                 # Inneholder HTML-maler spesifikke for 'accounts'-funksjonalitet
│   │   └── accounts/             # (f.eks., registreringsskjemaer, profilsider)
│   ├── tests/                      # Eksplisitt testmappe for 'accounts'-appen
│   │   ├── __init__.py             # Gjør 'tests'-mappen til en Python-pakke
│   │   ├── test_models.py          # Tester for 'accounts'-appens modeller
│   │   ├── test_views.py           # Tester for 'accounts'-appens views
│   │   └── ...                     # (andre testfiler)
│   └── views.py                    # Håndterer logikken for visninger relatert til brukerkonti
├── businesses/                       # Håndterer funksjonalitet spesifikk for bedrifter
│   ├── __init__.py                 # Gjør 'businesses'-mappen til en Python-pakke
│   ├── admin.py                    # Definisjoner for Django Admin-grensesnittet for businesses-modeller
│   ├── forms.py                    # Skjemaer relatert til bedriftsspesifikk funksjonalitet
│   ├── migrations/                 # Inneholder database-migrasjoner for 'businesses'-appen
│   │   └── ...                     # (f.eks., __init__.py og migrasjonsfiler)
│   ├── models.py                   # Definisjoner for datamodellene knyttet til bedrifter (utover BusinessProfile)
│   ├── permissions.py              # Definerer tilgangskontroller og rettigheter for 'businesses'-appen
│   ├── templates/                 # Inneholder HTML-maler spesifikke for 'businesses'-funksjonalitet
│   │   └── businesses/           # (f.eks., dashbord for bedrifter)
│   ├── tests/                      # Eksplisitt testmappe for 'businesses'-appen
│   │   ├── __init__.py             # Gjør 'tests'-mappen til en Python-pakke
│   │   ├── test_models.py          # Tester for 'businesses'-appens modeller
│   │   ├── test_views.py           # Tester for 'businesses'-appens views
│   │   └── ...                     # (andre testfiler)
│   └── views.py                    # Håndterer logikken for visninger relatert til bedrifter
├── giveaways/                        # Håndterer funksjonalitet knyttet til giveaways
│   ├── __init__.py                 # Gjør 'giveaways'-mappen til en Python-pakke
│   ├── admin.py                    # Definisjoner for Django Admin-grensesnittet for giveaways-modeller
│   ├── forms.py                    # Skjemaer relatert til opprettelse og deltakelse i giveaways
│   ├── migrations/                 # Inneholder database-migrasjoner for 'giveaways'-appen
│   │   └── ...                     # (f.eks., __init__.py og migrasjonsfiler)
│   ├── models.py                   # Definisjoner for datamodellene knyttet til giveaways (Event, Participation)
│   ├── permissions.py              # Definerer tilgangskontroller og rettigheter for 'giveaways'-appen
│   ├── templates/                 # Inneholder HTML-maler spesifikke for giveaways-funksjonalitet
│   │   └── giveaways/            # (f.eks., visning av giveaways, deltakelsesskjema)
│   ├── notifications.py           # Håndterer spesifikke meldinger relatert til giveaways
│   ├── tasks.py                    # Inneholder bakgrunnsoppgaver (f.eks., vinnertrekning) for giveaways
│   ├── tests/                      # Eksplisitt testmappe for 'giveaways'-appen
│   │   ├── __init__.py             # Gjør 'tests'-mappen til en Python-pakke
│   │   ├── test_models.py          # Tester for 'giveaways'-appens modeller
│   │   ├── test_views.py           # Tester for 'giveaways'-appens views
│   │   └── ...                     # (andre testfiler)
│   └── views.py                    # Håndterer logikken for visninger relatert til giveaways
├── notifications/                   # Generelt system for håndtering av уведомления
│   ├── __init__.py                 # Gjør 'notifications'-mappen til en Python-pakke
│   ├── emails.py                   # Spesifikk håndtering av e-postvarsler
│   ├── tests/                      # Eksplisitt testmappe for 'notifications'-appen
│   │   ├── __init__.py             # Gjør 'tests'-mappen til en Python-pakke
│   │   ├── test_models.py          # Tester for 'notifications'-appens modeller (hvis relevant)
│   │   ├── test_views.py           # Tester for 'notifications'-appens views (hvis relevant)
│   │   └── ...                     # (andre testfiler)
│   └── ...                         # (andre filer for varslingsmekanismer)
├── static/                         # Inneholder statiske filer (CSS, JavaScript, bilder)
│   └── ...                         # (organisert i undermapper)
├── templates/                      # Inneholder globale HTML-maler som brukes på tvers av appene
│   └── ...                         # (f.eks., base.html)
├── utils/                            # Inneholder gjenbrukbare hjelpefunksjoner og moduler
│   ├── __init__.py                 # Gjør 'utils'-mappen til en Python-pakke
│   ├── helpers.py                  # Diverse hjelpefunksjoner
│   └── logging.py                  # Konfigurasjon for logging
├── manage.py                       # Django-kommandolinjeverktøy for administrative oppgaver
└── requirements.txt                # Liste over Python-pakker som prosjektet er avhengig av
