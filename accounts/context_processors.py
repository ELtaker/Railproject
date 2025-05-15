from .permissions import user_is_member, user_is_business

def user_roles(request):
    user = request.user
    return {
        'is_member': user_is_member(user),
        'is_business': user_is_business(user),
    }
