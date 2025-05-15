from django.test import TestCase
from django.contrib.auth import get_user_model
from giveaways.models import Giveaway, Entry
from businesses.models import Business
from giveaways.forms import EntryForm
from giveaways.permissions import can_enter_giveaway
from django.utils import timezone
import datetime

User = get_user_model()
from django.contrib.auth.models import Group

class TestEntryForm(TestCase):
    def setUp(self):
        # Opprett business-bruker og business
        self.business_user = User.objects.create_user(
            username="bedrift", email="bedrift@test.com", password="test123",
            city="Oslo"
        )
        self.business = Business.objects.create(
            user=self.business_user, admin_id=self.business_user.id, name="TestBedrift", city="Oslo", postal_code="1234"
        )
        # Opprett medlem og ikke-medlem med unike brukernavn/e-post
        self.member = User.objects.create_user(
            username="medlem", email="medlem@test.com", password="test123",
            city="Oslo"
        )
        self.nonmember = User.objects.create_user(
            username="ikke", email="ikke@test.com", password="test123",
            city="Oslo"
        )
        # Medlemsgruppe
        members_group, _ = Group.objects.get_or_create(name="Members")
        self.member.groups.add(members_group)
        # Ikke legg self.nonmember i Members-gruppen

        # Opprett giveaway
        self.giveaway = Giveaway.objects.create(
            business=self.business,
            title="Test Giveaway",
            description="Test",
            start_date=timezone.now() - datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=1),
            is_active=True,
            signup_question="Hva er 2+2?",
            signup_options=["4", "5"]
        )


    def test_successful_entry_with_matching_city(self):
        form = EntryForm(data={"answer": "4", "user_location_city": "Oslo"}, giveaway=self.giveaway, request=None)
        self.assertTrue(form.is_valid())

    def test_entry_fails_with_wrong_city(self):
        form = EntryForm(data={"answer": "4", "user_location_city": "Bergen"}, giveaway=self.giveaway, request=None)
        self.assertFalse(form.is_valid())
        self.assertIn("user_location_city", form.errors)

    def test_entry_fails_without_city(self):
        form = EntryForm(data={"answer": "4"}, giveaway=self.giveaway, request=None)
        self.assertFalse(form.is_valid())
        self.assertIn("user_location_city", form.errors)

    def test_entry_fails_without_answer(self):
        form = EntryForm(data={"user_location_city": "Oslo"}, giveaway=self.giveaway, request=None)
        self.assertFalse(form.is_valid())
        self.assertIn("answer", form.errors)

    def test_entry_fallback_to_profile_city(self):
        request = type('obj', (object,), {"user": self.member, "method": "POST"})()
        form = EntryForm(data={"answer": "4"}, giveaway=self.giveaway, request=request)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user_location_city"], "Oslo")

    def test_double_entry_not_allowed(self):
        Entry.objects.create(giveaway=self.giveaway, user=self.member, answer="4", user_location_city="Oslo")
        self.assertFalse(can_enter_giveaway(self.member, self.giveaway))

    def test_non_member_cannot_enter(self):
        self.assertFalse(can_enter_giveaway(self.nonmember, self.giveaway))

    def test_business_user_cannot_enter(self):
        self.assertFalse(can_enter_giveaway(self.business_user, self.giveaway))

    def test_inactive_giveaway_blocks_entry(self):
        self.giveaway.is_active = False
        self.giveaway.save()
        self.assertFalse(can_enter_giveaway(self.member, self.giveaway))
