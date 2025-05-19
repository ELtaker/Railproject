# Raildrops - Django Web Application

Raildrops is a modular Django 5.2 web application for managing location-based giveaways, supporting both individual members and business users. Built with modern web practices, the platform allows businesses to create giveaways that members can participate in based on their geographical location. The project emphasizes clear separation of concerns, robust role-based permissions, accessibility, and a responsive user experience.

## Features

### User Management
- **Dual User Types:** Separate registration and authentication flows for members and businesses
- **Custom User Model:** Extended Django's user model with role-based functionality
- **Profile Management:** Dedicated profile management for both user types
- **Permission System:** Group-based permissions with Django's auth system

### Business Features
- **Business Dashboard:** Analytics and management interface for business owners
- **Business Profile:** Extended profiles with contact info, address, and social media links
- **Giveaway Creation:** Intuitive form for creating giveaways with customizable questions
- **Statistics:** Real-time reports on giveaway participation and engagement

### Giveaway System
- **Location-Based Participation:** Members must be in the same city as the business to participate
- **Question & Answer Validation:** Customizable questions with answer validation
- **Geolocation Integration:** Browser-based geolocation with OpenStreetMap reverse geocoding
- **Winner Selection:** Automated winner selection based on correct answers

### User Experience
- **Responsive Design:** Bootstrap 5-based interface that works on all devices
- **Accessibility:** ARIA attributes and keyboard navigation support
- **City-Based Filtering:** Find giveaways near your location
- **Dark/Light Mode:** Support for user preference in display mode

### Technical Features
- **Notification System:** Centralized notifications for user and business activities
- **RESTful URLs:** Consistent URL structure following kebab-case conventions
- **Form Validation:** Client and server-side validation with helpful error messages
- **Test Coverage:** Comprehensive unit and integration tests

## Technology Stack

- **Backend:** Django 5.2
- **Frontend:** Bootstrap 5, HTML5, CSS3, JavaScript
- **Database:** SQLite (development), PostgreSQL/MySQL (production)
- **Authentication:** Django's built-in auth with email backend
- **Geolocation:** HTML5 Geolocation API with OpenStreetMap Nominatim
- **Form Enhancement:** Django Widget Tweaks
- **Development Tools:** Docker, pre-commit hooks, pytest

## Application Structure

```
raildrops/
├── config/                # Django project configuration (settings, urls, wsgi, asgi)
├── accounts/              # User management, authentication, profiles
│   ├── migrations/        # Database migrations
│   ├── templates/         # Account-specific templates
│   ├── context_processors.py # Role-based context variables
│   ├── forms.py           # Registration and profile forms
│   ├── models.py          # User and member models
│   ├── permissions.py     # Role-based permission helpers
│   ├── urls.py            # URL patterns for accounts
│   └── views.py           # View controllers for accounts
├── businesses/            # Business profile management
│   ├── migrations/
│   ├── templates/
│   ├── forms.py           # Business registration and profile forms
│   ├── models.py          # Business models with location data
│   ├── urls.py            # URL patterns for businesses
│   └── views.py           # Business dashboard and profile views
├── giveaways/             # Giveaway functionality
│   ├── migrations/
│   ├── templates/
│   ├── forms.py           # Giveaway creation and participation forms
│   ├── models.py          # Giveaway, Entry, and Winner models
│   ├── permissions.py     # Access control helpers
│   ├── services.py        # Business logic and validation
│   ├── urls.py            # URL patterns for giveaways
│   └── views.py           # Giveaway views and form processing
├── notifications/         # Notification system
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── img/
├── templates/             # Base templates and includes
│   ├── base.html          # Base template with Bootstrap 5
│   └── includes/          # Reusable components (navbar, footer)
├── utils/                 # Utility modules and helpers
├── .env                   # Environment variables (not in version control)
├── .env.example           # Example environment configuration
├── requirements.txt       # Python dependencies
├── manage.py              # Django management script
└── README.md              # Project documentation
```

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Unix/MacOS: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure settings
6. Run migrations: `python manage.py migrate`
7. Create a superuser: `python manage.py createsuperuser`
8. Start the development server: `python manage.py runserver`

## Key Design Principles

- **Separation of Concerns:** Clear division between member and business functionality
- **DRY Code:** Reusable components and helper functions
- **Security First:** CSRF protection, input validation, and proper authentication
- **Accessibility:** ARIA attributes and semantic HTML throughout
- **Location Validation:** Geographical validation for giveaway participation
- **Progressive Enhancement:** Core functionality works without JavaScript

## Contributing

Please follow these guidelines when contributing to the project:

- Follow PEP 8 for Python code style
- Use kebab-case for URL patterns
- Add ARIA attributes for accessibility
- Write tests for new features
- Document code using docstrings

## Windsurf Compliance

Raildrops strictly adheres to the Windsurf project rules, ensuring consistency, quality, and best practices:

### Code Standards
- **PEP8 Compliance:** All Python code follows PEP8 style guidelines
- **Naming Conventions:**
  - Models: `lowercase_with_underscores`
  - Views: `CamelCase` for class-based views, `lowercase_with_underscores` for function-based views
  - URLs: `kebab-case-with-hyphens`
  - Templates: `lowercase_with_underscores.html`

### Architecture Compliance
- **Model-View-Template Pattern:** Strict separation between data, presentation, and business logic
- **ORM Usage:** No raw SQL; Django ORM used consistently for database operations
- **Role-Based Permissions:** Granular permission system for members vs businesses
- **Django Auth:** Leverages Django's built-in authentication with customization

### Accessibility & UX
- **Bootstrap 5 Integration:** Compliant with latest Bootstrap best practices
- **ARIA Attributes:** All interactive elements include proper accessibility attributes
- **Semantic HTML5:** Modern HTML5 tags used throughout the templates
- **Responsive Design:** Functions correctly on all screen sizes

### Security Practices
- **CSRF Protection:** All forms include CSRF tokens
- **XSS Mitigation:** Input sanitization and proper templating
- **Form Validation:** Both client and server-side validation
- **Django Middleware:** Appropriate security middleware enabled

## Location Features in Depth

### Geo-Validation System

One of Raildrops' core features is its location-based validation system that ensures members can only participate in giveaways located in their geographical area.

#### Location Matching Flow

1. **Business Registration:**
   - Businesses provide their physical address during registration
   - City and postal code are extracted and normalized
   - Location data is stored in the Business model

2. **Member Participation:**
   - When attempting to join a giveaway, members must share their location
   - Browser geolocation API captures coordinates (latitude/longitude)
   - OpenStreetMap Nominatim reverse geocoding converts coordinates to city names
   - City name is normalized and compared with the business location

3. **Validation Process:**
   - `cities_match()` function normalizes both locations (removing accents, spaces, case differences)
   - Cities must match exactly for participation to be allowed
   - Validation results are provided as immediate feedback to the user

#### Privacy Considerations

- Precise coordinates are never stored in the database
- Only city names are saved with participation records
- Geolocation prompts clearly explain why location is needed
- Members can manually enter their location if they prefer not to use browser geolocation

### Implementation Details

```python
# Example of city normalization and matching
def normalize_city(city: str) -> str:
    """Normalize city name for comparison (lowercase, no accents, no spaces)."""
    if not city:
        return ""
    city = city.lower().strip()
    city = unicodedata.normalize('NFKD', city)
    city = ''.join(c for c in city if c.isalnum())
    return city

def cities_match(user_city: str, business_city: str) -> bool:
    """Return True if cities match (robust, accent/space/case insensitive)."""
    return normalize_city(user_city) == normalize_city(business_city)
```

## Visual Documentation

### User Interface

#### Member View
```
+----------------------------------------------+
| RAILDROPS                        LOGIN SIGNUP |
+----------------------------------------------+
|                                              |
|  +------------------+  +------------------+  |
|  | GIVEAWAY 1       |  | GIVEAWAY 2       |  |
|  | Prize: Tech Item |  | Prize: Gift Card |  |
|  | Location: Oslo   |  | Location: Bergen |  |
|  | Ends: May 25     |  | Ends: June 1     |  |
|  +------------------+  +------------------+  |
|                                              |
|  +------------------+  +------------------+  |
|  | GIVEAWAY 3       |  | GIVEAWAY 4       |  |
|  | Prize: Tickets   |  | Prize: Discount  |  |
|  | Location: Oslo   |  | Location: Oslo   |  |
|  | Ends: May 30     |  | Ends: June 5     |  |
|  +------------------+  +------------------+  |
|                                              |
+----------------------------------------------+
```

#### Business Dashboard
```
+----------------------------------------------+
| RAILDROPS                            LOGOUT  |
| Dashboard | Giveaways | Profile | Analytics  |
+----------------------------------------------+
| STATISTICS                  CREATE GIVEAWAY  |
+----------------------------------------------+
| Active Giveaways: 3                          |
| Total Participants: 145                      |
| Pending Winners: 1                           |
+----------------------------------------------+
| RECENT ACTIVITY                              |
+----------------------------------------------+
| • New participant: Tech Giveaway (2 min ago) |
| • Giveaway ended: Spring Contest             |
| • Winner selected: Winter Promotion          |
+----------------------------------------------+
```

### Database Schema

```
+----------------+       +---------------+
| User           |       | Business      |
+----------------+       +---------------+
| id             |       | id            |
| email          |       | name          |
| username       |       | address       |
| password       |       | city          |
| is_active      |       | postal_code   |
| groups         +------->  owner (FK)    |
+----------------+       | contact_info  |
                        | social_media  |
+----------------+       +---------------+
| Entry          |             |
+----------------+             |
| id             |      +------v--------+
| user (FK)      |      | Giveaway      |
| giveaway (FK)  <------+ id            |
| answer         |      | business (FK) |
| location_city  |      | title         |
| date_entered   |      | prize_value   |
+----------------+      | question      |
                        | options       |
+----------------+      | start_date    |
| Winner         |      | end_date      |
+----------------+      | is_active     |
| id             |      +---------------+
| giveaway (FK)  <---+
| user (FK)      |
| selected_at    |
+----------------+
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Problem: NoReverseMatch Error in Templates
**Solution:** 
- Check URL patterns in urls.py for consistent kebab-case naming
- Verify namespace usage in URL tags `{% url 'namespace:name' %}`
- Ensure all referenced URLs actually exist in the URL configuration

#### Problem: Permission Denied for Member/Business Features
**Solution:**
- Verify user groups are properly assigned
- Check `is_member` and `is_business` helper functions
- Ensure attributes like `business_account` are being checked consistently

#### Problem: Geolocation Not Working
**Solution:**
- Browser must support Geolocation API
- User must grant location permissions
- HTTPS connection may be required (for production)
- Check browser console for errors from OpenStreetMap API

#### Problem: Bootstrap Styles Not Applied Correctly
**Solution:**
- Verify proper Bootstrap 5 CSS inclusion in base.html
- Check for custom CSS that might override Bootstrap
- Ensure correct class usage (e.g., .btn-primary vs .btn.primary)

### Debugging Tips

1. **Django Debug Toolbar:**
   - Install django-debug-toolbar for development
   - Monitor SQL queries, template rendering, and cache performance

2. **Console Logging:**
   - Check browser console for JavaScript errors
   - Review Django's development server output for Python errors

3. **Django Shell:**
   - Test model queries with `python manage.py shell`
   - Verify object relationships and attributes

4. **Template Debugging:**
   - Add `{{ debug }}` to templates to view available context variables
   - Use Django's template comments `{# comment #}` to disable sections

## Development Workflow

### Setting Up the Environment

1. **Create a development branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Activate the virtual environment:**
   ```bash
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Unix/macOS
   ```

3. **Run tests before making changes:**
   ```bash
   python manage.py test
   ```

### Development Process

1. **Make incremental changes with frequent commits**
2. **Follow the style guide:**
   - Run `black` and `flake8` before committing
   - Use descriptive commit messages

3. **Test your changes:**
   - Write unit tests for new features
   - Run the full test suite

4. **Document your work:**
   - Add docstrings to functions and classes
   - Update README if necessary

### Pull Request Process

1. **Create a pull request with a descriptive title**
2. **Include in the description:**
   - What problem does it solve?
   - How does it solve the problem?
   - Any migrations required?
   - Screenshots for UI changes

3. **Code review requirements:**
   - At least one approval required
   - All tests must pass
   - No conflicts with main branch

## Future Roadmap

### Planned Features

- **Multi-language Support:** Norwegian and English localization
- **Advanced Analytics:** Heatmaps of giveaway participation by region
- **Mobile App:** Native companion app for iOS and Android
- **Enhanced Notification System:** Push notifications and email digests
- **Social Sharing:** Integrated social media sharing for giveaways

### Enhancement Priorities

1. **Performance Optimization:** Database query optimization and caching
2. **API Development:** RESTful API for third-party integration
3. **Improved Testing:** Increase test coverage to >90%
4. **Documentation:** Complete API documentation and developer guides

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## User Roles & Models

- **Members:** Regular users who can join giveaways. Managed via Django Groups.
- **Businesses:** Users with a linked BusinessProfile. Can create and manage giveaways.
- **BusinessProfile:** Stores business info, location, and links to User.
- **Giveaway:** Represents a giveaway event, including title, description, location, question, answer options.
- **Participation:** Tracks member entries, selected answers, and timestamps. Ensures unique participation per giveaway.

## Giveaway Participation & Winner Selection

- Members can join active giveaways by answering a question.
- Only one entry per member per giveaway is allowed.
- Winner selection selects randomly among entries/participa.
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
