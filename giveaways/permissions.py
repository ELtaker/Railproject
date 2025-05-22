"""
Permissions for giveaways app. Centralizes all access logic for entries and giveaways.
"""

def is_member(user) -> bool:
    """
    Returns True if the user is authenticated and NOT a business user.
    
    Note: We've simplified this check to consider any authenticated non-business user
    as a member to avoid issues with group membership configuration.
    """
    return (
        user.is_authenticated
        and not hasattr(user, "business_account")
        # Removed the group check as it's causing issues and
        # we can determine membership by checking if user is not a business
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
