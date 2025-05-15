def user_is_member(user) -> bool:
    """
    Returnerer True hvis brukeren er autentisert, IKKE bedriftsbruker, og medlem av gruppen 'Members'.
    Brukes for å gi tilgang til medlemsfunksjoner.
    """
    return (
        user.is_authenticated
        and not hasattr(user, "business_profile")
        and user.groups.filter(name="Members").exists()
    )


def user_is_business(user) -> bool:
    """
    Returnerer True hvis brukeren er en bedriftsbruker.
    Nå: autentisert og har business_profile.
    Brukes for å gi tilgang til bedriftsfunksjoner.
    """
    return user.is_authenticated and hasattr(user, 'business_profile')

# Tester for permissions kan legges i tests/test_permissions.py
