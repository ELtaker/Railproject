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
            # Pre-fill the form data with the user's stored city
            if hasattr(self.request.user, "city") and self.request.user.city:
                # For initial data (GET request)
                self.initial["user_location_city"] = self.request.user.city
                
                # For POST data
                if self.request.method == "POST":
                    data = self.data.copy()
                    data["user_location_city"] = self.request.user.city
                    self.data = data

    def clean(self):
        from .services import validate_entry
        cleaned_data = super().clean()
        answer = cleaned_data.get("answer")
        user_location_city = cleaned_data.get("user_location_city")
        user = self.request.user if self.request else None
        giveaway = self.giveaway
        # Validate with business logic from services.py
        result = validate_entry(user, giveaway, user_location_city, answer)
        if not result["success"]:
            if "answer" in result.get("error", "").lower():
                self.add_error("answer", result["error"])
            else:
                self.add_error("user_location_city", result["error"])
            logger.warning(f"Validation failed for entry: {result['error']}")
        else:
            logger.info(f"Entry approved for city: {user_location_city}")
        return cleaned_data


class GiveawayCreateForm(forms.ModelForm):
    """
    Form for creating a new giveaway. Includes prize, image, value, description, dates,
    signup question and up to 4 answer options (radio).
    """
    option_1 = forms.CharField(label="Answer Option 1", max_length=100, required=False)
    option_2 = forms.CharField(label="Answer Option 2", max_length=100, required=False)
    option_3 = forms.CharField(label="Answer Option 3", max_length=100, required=False)
    option_4 = forms.CharField(label="Answer Option 4", max_length=100, required=False)
    
    def __init__(self, *args, **kwargs):
        self.business = kwargs.pop('business', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Giveaway
        fields = [
            "title", "description", "image", "prize_value", "start_date", "end_date", "signup_question"
        ]
        widgets = {
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        options = [
            cleaned_data.get("option_1"),
            cleaned_data.get("option_2"),
            cleaned_data.get("option_3"),
            cleaned_data.get("option_4"),
        ]
        options = [opt for opt in options if opt]
        if len(options) < 2:
            self.add_error("option_1", "You must provide at least 2 answer options.")
        if len(options) > 4:
            self.add_error("option_4", "Maximum 4 answer options are allowed.")
        cleaned_data["signup_options"] = options
        logger.info(f"Validated answer options: {options}")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        options = [
            self.cleaned_data.get("option_1"),
            self.cleaned_data.get("option_2"),
            self.cleaned_data.get("option_3"),
            self.cleaned_data.get("option_4"),
        ]
        instance.signup_options = [opt for opt in options if opt]
        if commit:
            instance.save()
        return instance
