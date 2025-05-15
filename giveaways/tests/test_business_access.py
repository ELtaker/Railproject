from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from businesses.models import Business
from giveaways.models import Giveaway

User = get_user_model()

class GiveawayBusinessAccessTest(TestCase):
    def setUp(self):
        self.member = User.objects.create_user(username="member", email="member@test.com", password="test123")
        self.business_user = User.objects.create_user(username="biz", email="biz@test.com", password="test123")
        self.business = Business.objects.create(user=self.business_user, admin=self.business_user, name="TestBedrift")


    def test_member_cannot_access_giveaway_create(self):
        self.client.login(email="member@test.com", password="test123")
        response = self.client.get(reverse('giveaways:giveaway_create'))
        self.assertRedirects(response, reverse('accounts:profile'))

    def test_business_can_access_giveaway_create(self):
        self.client.login(email="biz@test.com", password="test123")
        response = self.client.get(reverse('giveaways:giveaway_create'))
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_access_business_dashboard(self):
        self.client.login(email="member@test.com", password="test123")
        response = self.client.get(reverse('accounts:business_dashboard'))
        self.assertRedirects(response, reverse('accounts:profile'))

    def test_business_can_access_business_dashboard(self):
        self.client.login(email="biz@test.com", password="test123")
        response = self.client.get(reverse('accounts:business_dashboard'))
        self.assertEqual(response.status_code, 200)
