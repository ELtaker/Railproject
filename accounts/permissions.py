def user_is_member(user) -> bool:
    """
    Returnerer True hvis brukeren er autentisert, IKKE bedriftsbruker, og medlem av gruppen 'Members'.
    """
    return (
        user.is_authenticated
        and not hasattr(user, "business_profile")
        and user.groups.filter(name="Members").exists()
    )



def user_is_business(user) -> bool:
    """Returnerer True hvis brukeren er en bedriftsbruker.
    Nå: autentisert og har business_profile.
    """
    return user.is_authenticated and hasattr(user, 'business_profile')
