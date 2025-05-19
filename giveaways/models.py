from django.db import models
from django.conf import settings
from businesses.models import Business

class Giveaway(models.Model):
    """
    Model for giveaways on Raildrops.
    Includes prize, image, value, description, dates, signup question and answer options.
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="giveaways")
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="giveaway_images/", blank=True, null=True)
    prize_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prize Value", null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    signup_question = models.CharField(max_length=255, blank=True, verbose_name="Signup Question")
    signup_options = models.JSONField(blank=True, null=True, verbose_name="Answer Options (max 4)")

    def __str__(self) -> str:
        return f"{self.title} ({self.business.name})"

class Entry(models.Model):
    """
    Entry for a giveaway. Stores user, giveaway, selected answer and user's city (from geolocation).
    """
    giveaway = models.ForeignKey(Giveaway, on_delete=models.CASCADE, related_name="entries")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entries")
    answer = models.CharField(max_length=255, blank=True)
    user_location_city = models.CharField(max_length=100, blank=True)
    entered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('giveaway', 'user')

    def __str__(self) -> str:
        return f"{self.user.email} - {self.giveaway.title} ({self.user_location_city})"

class Winner(models.Model):
    giveaway = models.OneToOneField(Giveaway, on_delete=models.CASCADE, related_name="winner")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    selected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Winner: {self.user.email} for {self.giveaway.title}"