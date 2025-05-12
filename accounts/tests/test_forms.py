import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from accounts.forms import (
    UserRegistrationForm, CompanyRegistrationForm, BusinessRegistrationForm,
    MemberLoginForm, CompanyLoginForm, UserProfileForm
)
from accounts.models import Company

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
def test_company_registration_form_valid():
    form = CompanyRegistrationForm(data={
        'company_name': 'TestCo',
        'organization_number': '123456789',
        'email': 'testco@example.com',
        'password1': 'firmapass123',
        'password2': 'firmapass123',
    })
    assert form.is_valid(), form.errors
    company = form.save()
    assert company.company_name == 'TestCo'
    assert company.check_password('firmapass123')

@pytest.mark.django_db
def test_company_registration_form_duplicate_email():
    Company.objects.create(company_name='TestCo2', organization_number='987654321', email='dup@example.com')
    form = CompanyRegistrationForm(data={
        'company_name': 'TestCo3',
        'organization_number': '123123123',
        'email': 'dup@example.com',
        'password1': 'firmapass123',
        'password2': 'firmapass123',
    })
    assert not form.is_valid()
    assert 'allerede i bruk' in str(form.errors)

@pytest.mark.django_db
def test_member_login_form_invalid():
    form = MemberLoginForm(data={
        'email': 'notfound@example.com',
        'password': 'wrongpass',
    })
    assert not form.is_valid()
    assert 'Ugyldig e-post eller passord' in str(form.errors)

@pytest.mark.django_db
def test_company_login_form_invalid():
    form = CompanyLoginForm(data={
        'email': 'notfound@example.com',
        'password': 'wrongpass',
    })
    assert not form.is_valid()
    assert 'Ugyldig e-post eller passord for bedrift' in str(form.errors)

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
