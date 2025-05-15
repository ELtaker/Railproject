import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from accounts.forms import (
    UserRegistrationForm, BusinessRegistrationForm,
    MemberLoginForm, UserProfileForm
)

User = get_user_model()

@pytest.mark.django_db
def test_user_registration_form_valid():
    form = UserRegistrationForm(data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password1': 'testpassword123',
        'password2': 'testpassword123',
    })
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.username == 'testuser'
    assert user.check_password('testpassword123')
    assert user.is_authenticated

@pytest.mark.django_db
def test_user_registration_form_password_mismatch():
    form = UserRegistrationForm(data={
        'username': 'testuser2',
        'email': 'testuser2@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password1': 'abc123',
        'password2': 'wrongpass',
    })
    assert not form.is_valid()
    assert 'Passordene matcher ikke.' in str(form.errors)

@pytest.mark.django_db
def test_member_login_form_invalid():
    form = MemberLoginForm(data={
        'email': 'notfound@example.com',
        'password': 'wrongpass',
    })
    assert not form.is_valid()
    assert 'Ugyldig e-post eller passord' in str(form.errors)

@pytest.mark.django_db
def test_user_profile_form_email_unique():
    user1 = User.objects.create_user(username='user1', email='unique@example.com', password='pw12345')
    user2 = User.objects.create_user(username='user2', email='other@example.com', password='pw12345')
    form = UserProfileForm(instance=user2, data={
        'email': 'unique@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'city': 'Oslo',
    })
    assert not form.is_valid()
    assert 'allerede i bruk' in str(form.errors)
