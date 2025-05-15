import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client


User = get_user_model()

@pytest.mark.django_db
def test_member_register_view(client):
    url = reverse('accounts:member-register')
    response = client.get(url)
    assert response.status_code == 200
    # Prøv registrering
    data = {
        'username': 'viewuser',
        'email': 'viewuser@example.com',
        'first_name': 'View',
        'last_name': 'User',
        'password1': 'viewpass123',
        'password2': 'viewpass123',
    }
    response = client.post(url, data)
    assert response.status_code == 302
    assert User.objects.filter(username='viewuser').exists()

@pytest.mark.django_db
def test_member_login_view(client):
    user = User.objects.create_user(username='loginuser', email='login@example.com', password='pw12345')
    url = reverse('accounts:member-login')
    response = client.get(url)
    assert response.status_code == 200
    response = client.post(url, {'email': 'login@example.com', 'password': 'pw12345'}, follow=True)
    # Sjekk at siste redirect går til dashboard og status er 200
    if response.redirect_chain:
        last_url, last_status = response.redirect_chain[-1]
        assert 'dashboard' in last_url and last_status == 302
    assert response.status_code == 200


@pytest.mark.django_db
def test_business_register_view(client):
    url = reverse('accounts:business-register')
    response = client.get(url)
    assert response.status_code == 200
    data = {
        'email': 'bedrift@example.com',
        'first_name': 'Bedrift',
        'last_name': 'Test',
        'company_name': 'Testfirma AS',
        'organization_number': '123456789',
        'address': 'Testveien 1',
        'postal_code': '1234',
        'city': 'Testby',
        'password1': 'testpass123',
        'password2': 'testpass123',
    }
    response = client.post(url, data)
    assert response.status_code == 302
    from accounts.models import User, BusinessProfile
    user = User.objects.filter(email='bedrift@example.com').first()
    assert user is not None
    assert hasattr(user, 'business_profile')
    assert user.business_profile.company_name == 'Testfirma AS'

    # Test valideringsfeil (duplikat org.nr)
    response = client.post(url, {**data, 'email': 'ny@bedrift.no'})
    assert response.status_code == 200
    assert b"allerede i bruk" in response.content

@pytest.mark.django_db
def test_member_login_view_invalid_password(client):
    user = User.objects.create_user(username='loginuser', email='login@example.com', password='pw12345')
    url = reverse('accounts:member-login')
    response = client.get(url)
    assert response.status_code == 200
    response = client.post(url, {'email': 'login@example.com', 'password': 'pw12345'}, follow=True)
    # Sjekk at siste redirect går til dashboard og status er 200
    if response.redirect_chain:
        last_url, last_status = response.redirect_chain[-1]
        assert 'dashboard' in last_url and last_status == 302
    assert response.status_code == 200
    # Test feil passord
    response = client.post(url, {'email': 'login@example.com', 'password': 'feilpass'}, follow=True)
    assert b"Ugyldig e-post eller passord" in response.content

def test_dashboard_requires_login(client):
    url = reverse('accounts:dashboard')
    response = client.get(url)
    # Bør redirecte til login
    assert response.status_code in (302, 401)
