from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

# Get the User model
User = get_user_model()

# Get or create the Members group
print('Checking for Members group...')
members_group, created = Group.objects.get_or_create(name='Members')
print(f'Members group {"created" if created else "exists"}')

# Find the user
user = User.objects.get(email='eivind@hotmail.com')
print(f'Found user: {user.email}')

# Check if user is already in the Members group
if user.groups.filter(name='Members').exists():
    print('User is already in Members group')
else:
    user.groups.add(members_group)
    print('Added user to Members group')
