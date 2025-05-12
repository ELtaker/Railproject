import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client
from accounts.models import Company

User = get_user_model()

@pytest.mark.django_db
def test_member_register_view(client):
    url = reverse('accounts:member_register')
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
    url = reverse('accounts:member_login')
    response = client.get(url)
    assert response.status_code == 200
    response = client.post(url, {'email': 'login@example.com', 'password': 'pw12345'}, follow=True)
    # Sjekk at siste redirect går til dashboard og status er 200
    if response.redirect_chain:
        last_url, last_status = response.redirect_chain[-1]
        assert 'dashboard' in last_url and last_status == 302
    assert response.status_code == 200

@pytest.mark.django_db
def test_company_register_view(client):
    url = reverse('accounts:company_register')
    response = client.get(url)
    assert response.status_code == 200
    data = {
        'company_name': 'TestBedrift',
        'organization_number': '999888777',
        'email': 'bedrift@example.com',
        'password1': 'bedriftpass123',
        'password2': 'bedriftpass123',
    }
    response = client.post(url, data)
    assert response.status_code in (302, 200)
    assert Company.objects.filter(company_name='TestBedrift').exists()

@pytest.mark.django_db
def test_dashboard_requires_login(client):
    url = reverse('accounts:dashboard')
    response = client.get(url)
    # Bør redirecte til login
    assert response.status_code in (302, 401)
