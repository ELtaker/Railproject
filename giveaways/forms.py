from django import forms
from .models import Giveaway, Entry
import logging

logger = logging.getLogger(__name__)

class EntryForm(forms.ModelForm):
    answer = forms.CharField(label="Answer", widget=forms.RadioSelect, required=True)
    user_location_city = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = Entry
        fields = ["answer", "user_location_city"]

    def __init__(self, *args, **kwargs):
        self.giveaway = kwargs.pop("giveaway", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # Dynamic choices for radio buttons from giveaway
        if self.giveaway and self.giveaway.signup_options:
            self.fields["answer"].widget = forms.RadioSelect(choices=[(opt, opt) for opt in self.giveaway.signup_options])
            
        # Always set the location from the user profile
        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            
            # Try to get city from User model first
            user_city = user.city if hasattr(user, "city") else ""
            
            # If no city found, try to get from MemberProfile
            if not user_city and hasattr(user, "member_profile"):
                try:
                    user_city = user.member_profile.city or ""
                except Exception:
                    # Handle case where profile doesn't exist or has no city
                    user_city = ""
            
            # Use the city if we found one
            if user_city:
                # For initial data (GET request)
                self.initial["user_location_city"] = user_city
                
                # For POST data
                if self.request.method == "POST":
                    data = self.data.copy()
                    data["user_location_city"] = user_city
                    self.data = data
                    
                # Log the city we're using
                logger.info(f"Using city {user_city} for user {user.email}")
            else:
                logger.warning(f"No city found for user {user.email}")

    def clean(self):
        cleaned_data = super().clean()
        answer = cleaned_data.get("answer")
        user_location_city = cleaned_data.get("user_location_city")
        user = self.request.user if self.request else None
        giveaway = self.giveaway
        
        # Direct implementation of validation logic to avoid circular imports
        result = self._validate_entry(user, giveaway, user_location_city, answer)
        
        if not result["success"]:
            if "answer" in result.get("error", "").lower():
                self.add_error("answer", result["error"])
            else:
                self.add_error("user_location_city", result["error"])
            logger.warning(f"Validation failed for entry: {result['error']}")
        else:
            logger.info(f"Entry approved for city: {user_location_city}")
        return cleaned_data
        
    def _validate_entry(self, user, giveaway, user_city, answer):
        """Internal validation function to avoid circular imports."""
        # Always require an answer
        if not answer:
            return {"success": False, "error": "You must select an answer."}
        
        # Always require a city location
        if not user_city:
            return {"success": False, "error": "Your location must be registered. Allow location sharing or enter city manually."}
        
        # IMPORTANT: Users must be in the same city as the business to participate
        normalized_user_city = self._normalize_city(user_city)
        normalized_business_city = self._normalize_city(giveaway.business.city)
        
        # Log the normalization for debugging
        logger.info(f"Comparing user city '{user_city}' ({normalized_user_city}) with business city '{giveaway.business.city}' ({normalized_business_city})")
        
        if not normalized_user_city:
            # Edge case: Empty normalized city
            return {"success": False, "error": f"Invalid city format: {user_city}. Please update your profile with a valid city."}
        
        if normalized_user_city != normalized_business_city:
            # Create a more informative error message
            return {
                "success": False, 
                "error": f"You must be in {giveaway.business.city} to participate in this giveaway. Your current position is registered as {user_city}."
            }
        
        # Log successful location match
        logger.info(f"Approved position: {user_city} matches {giveaway.business.city}")
        
        return {"success": True, "normalized_city": normalized_user_city}
    
    def _normalize_city(self, city):
        """Normalize city name for consistent comparison."""
        import unicodedata
        if not city:
            return ""
        city = city.lower().strip()
        city = unicodedata.normalize('NFKD', city)
        # Remove all non-alphanumeric characters
        city = ''.join(c for c in city if c.isalnum())
        return city


class GiveawayCreateForm(forms.ModelForm):
    """
    Form for creating a new giveaway. Includes prize, image, value, description, dates,
    signup question and up to 4 answer options (radio).
    """
    option_1 = forms.CharField(label="Answer Option 1", max_length=100, required=False)
    option_2 = forms.CharField(label="Answer Option 2", max_length=100, required=False)
    option_3 = forms.CharField(label="Answer Option 3", max_length=100, required=False)
    option_4 = forms.CharField(label="Answer Option 4", max_length=100, required=False)
    signup_options = forms.JSONField(required=False, widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Giveaway
        fields = [
            "title", "description", "image", "prize_value", "start_date", "end_date", "signup_question", "signup_options"
        ]
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        
        if start_date and end_date and start_date >= end_date:
            self.add_error("end_date", "End date must be after start date")
            
        if not self.business:
            self.add_error(None, "A business must be associated with this giveaway")
        
        # Ensure at least two options are provided
        option_1 = cleaned_data.get("option_1")
        option_2 = cleaned_data.get("option_2")
        if not (option_1 and option_2):
            self.add_error("option_1", "You must provide at least two answer options.")
            self.add_error("option_2", "You must provide at least two answer options.")
        
        # Create signup_options list for validation
        options = [
            cleaned_data.get("option_1"),
            cleaned_data.get("option_2"),
            cleaned_data.get("option_3"),
            cleaned_data.get("option_4"),
        ]
        # Filter out empty options
        options_list = [opt for opt in options if opt]
        
        if not options_list:
            self.add_error(None, "Du må angi svaralternativer til spørsmålet.")
        
        # Set the signup_options field value
        cleaned_data["signup_options"] = options_list
        
        return cleaned_data

    def save(self, commit=True):
        # We've already set signup_options in clean(), so we can use the default behavior
        return super().save(commit=commit)
