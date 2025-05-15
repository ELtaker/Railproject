import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.edit import UpdateView
from django.views.generic import DetailView
from .models import Business


logger = logging.getLogger(__name__)

class BusinessPublicProfileView(DetailView):
    """
    Offentlig visning av bedriftsprofil. Viser navn, logo, beskrivelse, sted, postnummer, nettside og aktive giveaways.
    """
    model = Business
    template_name = "businesses/business_public_profile.html"
    context_object_name = "business"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_object()
        giveaways = business.giveaways.filter(is_active=True)
        context["giveaways"] = giveaways
        user = self.request.user
        context["can_create_giveaway"] = user.is_authenticated and hasattr(user, "business_account") and user.business_account.pk == business.pk
        return context


class BusinessProfileView(LoginRequiredMixin, UpdateView):
    """
    View for visning og redigering av bedriftsprofil.
    Kun tilgjengelig for innloggede bedriftsbrukere.
    """
    model = Business
    # Forutsetter at det finnes en BusinessForm i businesses/forms.py
    from .forms import BusinessForm
    form_class = BusinessForm
    template_name = "businesses/business_profile.html"
    success_url = reverse_lazy("business_profile")
    login_url = "login"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, "business_account"):
            logger.warning(f"Bruker {user.username} forsøkte å åpne bedriftsprofil uten å være bedriftsbruker.")
            messages.error(request, "Du har ikke tilgang til bedriftsprofil.")
            return redirect("accounts:profile")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user.business_account

    def form_valid(self, form):
        logger.info(f"Bedriftsprofil oppdatert for {self.request.user.username}")
        messages.success(self.request, "Bedriftsprofilen er oppdatert!")
        return super().form_valid(form)

