import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.edit import UpdateView, FormView
from django.views.generic import DetailView, TemplateView
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.db.models import Count, Q
from .models import Business
from .forms import BusinessForm
from accounts.forms import BusinessRegistrationForm, MemberLoginForm

logger = logging.getLogger(__name__)


class BusinessContextMixin:
    """
    Mixin providing common functionality for business-related views.
    Includes methods for calculating statistics and preparing context.
    """
    def get_business(self):
        """
        Retrieves the business object for the logged-in user.
        """
        user = self.request.user
        return getattr(user, 'business_account', None)
        
    def get_business_stats(self):
        """
        Calculates statistics for a business: giveaways, participants, winners.
        Returns a dict with key metrics.
        """
        business = self.get_business()
        if not business:
            return {}
            
        from giveaways.models import Giveaway, Entry, Winner
        
        # At-a-glance stats
        giveaways = Giveaway.objects.filter(business=business)
        giveaways_active = giveaways.filter(is_active=True)
        giveaways_ended = giveaways.filter(is_active=False)
        total_giveaways = giveaways.count()
        total_participants = Entry.objects.filter(giveaway__business=business).count()
        total_winners = Winner.objects.filter(giveaway__business=business).count()
        
        # Recent activity
        recent_giveaways = giveaways.order_by('-created_at')[:5]
        recent_winners = Winner.objects.filter(
            giveaway__business=business
        ).select_related('user', 'giveaway').order_by('-selected_at')[:5]
        
        return {
            "giveaways_active": giveaways_active,
            "giveaways_ended": giveaways_ended,
            "total_giveaways": total_giveaways,
            "total_participants": total_participants,
            "total_winners": total_winners,
            "recent_giveaways": recent_giveaways,
            "recent_winners": recent_winners,
        }

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

class BusinessRegisterView(FormView):
    template_name = "accounts/business_register.html"
    form_class = BusinessRegistrationForm
    success_url = reverse_lazy("businesses:business-login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.save()
        business = Business.objects.create(
            user=user,
            admin=user,
            name=form.cleaned_data["company_name"],
            organization_number=form.cleaned_data["organization_number"],
            postal_code=form.cleaned_data["postal_code"],
            city=form.cleaned_data["city"]
        )
        # Add user to Bedrift group
        from django.contrib.auth.models import Group
        bedrift_group, _ = Group.objects.get_or_create(name="Bedrift")
        user.groups.add(bedrift_group)
        business.admin = user
        business.save()
        messages.success(self.request, "Bedriftsbruker og bedrift opprettet!")
        return super().form_valid(form)

class BusinessLoginView(FormView):
    template_name = "accounts/business_login.html"
    form_class = MemberLoginForm

    def form_valid(self, form):
        user = form.cleaned_data.get('user')
        if not hasattr(user, 'business_account') or not user.business_account:
            messages.error(self.request, "Denne brukeren har ikke tilknyttet bedrift. Bruk medlemsinnlogging om du ikke er bedriftsbruker.")
            return self.form_invalid(form)
        login(self.request, user)
        messages.success(self.request, "Velkommen, bedriftsbruker!")
        return HttpResponseRedirect(reverse('accounts:business-dashboard'))

class BusinessProfileView(LoginRequiredMixin, UpdateView):
    """
    View for visning og redigering av bedriftsprofil.
    Kun tilgjengelig for innloggede bedriftsbrukere.
    """
    model = Business
    form_class = BusinessForm
    template_name = "businesses/business_profile_edit.html"
    success_url = reverse_lazy("businesses:business-profile")
    login_url = "businesses:business-login"

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


class BusinessProfileEditView(LoginRequiredMixin, BusinessContextMixin, UpdateView):
    """
    View for redigering av bedriftsprofil med utvidede funksjoner.
    Bygger på BusinessContextMixin for tilgang til statistikk og bedriftsdata.
    Kun tilgjengelig for innloggede bedriftsbrukere.
    """
    model = Business
    form_class = BusinessForm
    template_name = "businesses/business_profile_edit.html"
    success_url = reverse_lazy("businesses:business-profile")
    login_url = "businesses:business-login"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, "business_account"):
            logger.warning(f"Bruker {user.username} forsøkte å redigere bedriftsprofil uten å være bedriftsbruker.")
            messages.error(request, "Du har ikke tilgang til å redigere bedriftsprofil.")
            return redirect("accounts:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.get_business()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Legg til statistikk hvis det er ønskelig i redigeringsvisningen
        # context.update(self.get_business_stats())
        return context

    def form_valid(self, form):
        logger.info(f"Bedriftsprofil oppdatert for {self.request.user.username} via redigeringsvisning")
        messages.success(self.request, "Bedriftsprofilen er oppdatert!")
        return super().form_valid(form)

class BusinessDashboardView(LoginRequiredMixin, BusinessContextMixin, TemplateView):
    """
    Dashboard for bedriftsbrukere. Viser statistikk, aktive/avsluttede giveaways
    og nylig aktivitet. Bruker BusinessContextMixin for statistikk.
    """
    template_name = "businesses/business_dashboard.html"
    login_url = "businesses:business-login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_business()
        
        # Legg til business først slik at det alltid er tilgjengelig i templaten
        context["business"] = business
        
        # Hent statistikk fra mixin-metode
        stats = self.get_business_stats()
        context.update(stats)
        
        return context