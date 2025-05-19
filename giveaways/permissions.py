"""
Permissions for giveaways app. Centralizes all access logic for entries and giveaways.
"""

def is_member(user) -> bool:
    """
    Returns True if the user is authenticated, NOT a business user, and a member of the 'Members' group.
    """
    return (
        user.is_authenticated
        and not hasattr(user, "business_account")
        and user.groups.filter(name="Members").exists()
    )



def can_enter_giveaway(user, giveaway) -> bool:
    """Return True if user is allowed to enter the given giveaway."""
    if not user.is_authenticated:
        return False
    if not is_member(user):
        return False
    if not giveaway.is_active:
        return False
    # Only allow one entry per user per giveaway
    if giveaway.entries.filter(user=user).exists():
        return False
    return True
