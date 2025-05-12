from django import forms
from .models import Giveaway, Entry
import logging

logger = logging.getLogger(__name__)

class EntryForm(forms.ModelForm):
    answer = forms.CharField(label="Svar", widget=forms.RadioSelect, required=True)
    user_location_city = forms.CharField(widget=forms.HiddenInput, required=True)

    class Meta:
        model = Entry
        fields = ["answer", "user_location_city"]

    def __init__(self, *args, **kwargs):
        self.giveaway = kwargs.pop("giveaway", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # Dynamisk valg for radio fra giveaway
        if self.giveaway and self.giveaway.signup_options:
            self.fields["answer"].widget = forms.RadioSelect(choices=[(opt, opt) for opt in self.giveaway.signup_options])
        # Hvis POST og feltet mangler, sett det fra profil
        if self.request and self.request.method == "POST":
            data = self.data.copy()
            if not data.get("user_location_city") and hasattr(self.request.user, "city") and self.request.user.city:
                data["user_location_city"] = self.request.user.city
                self.data = data

    def clean(self):
        from .services import validate_entry
        cleaned_data = super().clean()
        answer = cleaned_data.get("answer")
        user_location_city = cleaned_data.get("user_location_city")
        user = self.request.user if self.request else None
        giveaway = self.giveaway
        # Valider med businesslogikk fra services.py
        result = validate_entry(user, giveaway, user_location_city, answer)
        if not result["success"]:
            if "answer" in result.get("error", "").lower():
                self.add_error("answer", result["error"])
            else:
                self.add_error("user_location_city", result["error"])
            logger.warning(f"Validering feilet for entry: {result['error']}")
        else:
            logger.info(f"Påmelding godkjent for by: {user_location_city}")
        return cleaned_data


class GiveawayCreateForm(forms.ModelForm):
    """
    Skjema for å opprette en ny giveaway. Inkluderer premie, bilde, verdi, beskrivelse, datoer,
    påmeldingsspørsmål og opptil 4 svaralternativer (radio).
    """
    option_1 = forms.CharField(label="Svaralternativ 1", max_length=100, required=False)
    option_2 = forms.CharField(label="Svaralternativ 2", max_length=100, required=False)
    option_3 = forms.CharField(label="Svaralternativ 3", max_length=100, required=False)
    option_4 = forms.CharField(label="Svaralternativ 4", max_length=100, required=False)

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
            self.add_error("option_1", "Du må oppgi minst 2 svaralternativer.")
        if len(options) > 4:
            self.add_error("option_4", "Maks 4 svaralternativer er tillatt.")
        cleaned_data["signup_options"] = options
        logger.info(f"Validerte svaralternativer: {options}")
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
