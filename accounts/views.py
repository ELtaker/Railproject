import logging
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView

from .forms import UserRegistrationForm, UserProfileForm, BusinessRegistrationForm, MemberLoginForm
from .permissions import user_is_member, user_is_business
from businesses.forms import BusinessForm as BusinessProfileForm
from businesses.models import Business
from giveaways.models import Entry, Winner, Giveaway
from giveaways.views import BusinessOnlyMixin

User = get_user_model()
logger = logging.getLogger(__name__)

from django.views.generic.edit import FormView

class BusinessDashboardView(LoginRequiredMixin, BusinessOnlyMixin, TemplateView):
    template_name = "businesses/business_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.request.user.business_account
        context["business"] = business
        context["giveaways_active"] = Giveaway.objects.filter(business=business, is_active=True)
        context["giveaways_ended"] = Giveaway.objects.filter(business=business, is_active=False)
        return context


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
        # Du kan tilpasse redirect til bedriftsdashboard eller profil
        return HttpResponseRedirect(reverse('accounts:business_dashboard'))

class HomeTestPageView(TemplateView):
    """
    Viser forsiden (testpage.html) med alle aktive giveaways horisontalt.
    """
    template_name = "testpage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        giveaways = Giveaway.objects.filter(is_active=True).select_related('business')
        context["giveaways"] = giveaways
        logger.info(f"Forside med {giveaways.count()} giveaways vist.")
        return context

class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Viser medlemsprofil for innloggede brukere.
    Krever innlogging.
    """
    template_name = "accounts/profile.html"
    login_url = "accounts:member-login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user type context for accessibility improvements
        context['is_member'] = user_is_member(self.request.user)
        context['is_business'] = user_is_business(self.request.user)
        logger.info(f"Profilside vist for bruker: {self.request.user.username}")
        return context

class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Lar medlem redigere sin profil (e-post, navn, bilde).
    Krever innlogging.
    """
    model = User
    form_class = UserProfileForm
    template_name = "accounts/profile_edit.html"
    success_url = reverse_lazy("accounts:member-profile")
    login_url = "accounts:member-login"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        logger.info(f"Profil oppdatert for bruker: {self.request.user.username}")
        messages.success(self.request, "Profilen din er oppdatert!")
        return super().form_valid(form)


class BusinessProfileEditView(LoginRequiredMixin, BusinessOnlyMixin, UpdateView):
    """
    Lar bedriftsbruker redigere sin bedriftsprofil.
    Krever innlogging og bedriftsrolle.
    """
    model = Business
    form_class = BusinessProfileForm
    template_name = "businesses/business_profile_edit.html"
    success_url = reverse_lazy("accounts:business-dashboard")
    login_url = "accounts:member-login"

    def get_object(self, queryset=None):
        return self.request.user.business_account

    def form_valid(self, form):
        logger.info(f"Bedriftsprofil oppdatert for: {self.request.user.business_account}")
        messages.success(self.request, "Bedriftsprofilen er oppdatert!")
        return super().form_valid(form)

class BusinessRegisterView(FormView):
    """
    View for registrering av bedriftsbrukere og tilknyttet bedrift på Raildrops.
    Viser skjema, validerer input og oppretter både bruker og Business.
    """
    template_name = "accounts/business_register.html"
    form_class = BusinessRegistrationForm
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        from django.contrib.auth.models import Group
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.save()
        # Opprett Business-instans
        business = Business.objects.create(
            user=user,
            admin=user,
            name=form.cleaned_data["company_name"],
            organization_number=form.cleaned_data["organization_number"],
            postal_code=form.cleaned_data["postal_code"],
            city=form.cleaned_data["city"]
        )
        # Legg bruker i Bedrift-gruppen
        bedrift_group, _ = Group.objects.get_or_create(name="Bedrift")
        user.groups.add(bedrift_group)
        # Sett bruker som admin for bedriften
        business.admin = user
        business.save()
        return super().form_valid(form)

class UserRegisterView(FormView):
    """
    View for registrering av nye medlemmer på Raildrops.
    Viser registreringsskjema, validerer input og oppretter ny bruker.
    """
    template_name = "accounts/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        from django.contrib.auth.models import Group
        user = form.save()
        # Opprett MemberProfile
        from .models import MemberProfile
        MemberProfile.objects.create(user=user)
        # Legg bruker i Medlem-gruppen
        medlem_group, _ = Group.objects.get_or_create(name="Medlem")
        user.groups.add(medlem_group)
        # Spesifiser backend for vanlige brukere
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        logger.info(f"Bruker registrert: {user.username} ({user.email})")
        messages.success(self.request, "Bruker registrert og innlogget!")
        return redirect('accounts:dashboard')

def member_login_view(request):
    """
    Håndterer innlogging for medlemmer.
    Validerer innloggingsdata, logger inn brukeren og viser relevante meldinger.
    Inkluderer ARIA-attributter og andre tilgjengelighetsforbedringer.
    """
    if request.method == 'POST':
        form = MemberLoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.cleaned_data['user'])
            messages.success(request, "Du er nå logget inn som medlem.")
            return redirect('accounts:dashboard')
    else:
        form = MemberLoginForm()
        
    # Legg til ARIA attributter på form fields for bedre tilgjengelighet
    if hasattr(form, 'fields'):
        for field in form.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({
                    'class': 'form-control',
                    'aria-required': 'true' if field.required else 'false'
                })
    
    return render(request, 'accounts/member_login.html', {'form': form})





def custom_logout_view(request):
    logout(request)
    messages.success(request, "Du er nå logget ut.")
    return redirect('home')

# BusinessProfileEditView er fjernet. Bruk bedriftsprofil-redigering fra businesses/views.py.
    model = Business
    form_class = BusinessProfileForm
    template_name = "businesses/business_profile_edit.html"
    success_url = "/accounts/dashboard/"
    login_url = "login"

    def get_object(self, queryset=None):
        # Finn Business-profil for innlogget bruker
        try:
            return Business.objects.get(user=self.request.user)
        except Business.DoesNotExist:
            from django.http import Http404
            raise Http404("Ingen bedriftsprofil funnet for denne brukeren.")

    def form_valid(self, form):
        messages.success(self.request, "Bedriftsprofilen er oppdatert!")
        return super().form_valid(form)

@login_required
def dashboard_view(request):
    """
    Viser dashboard for innlogget bruker. 
    For vanlige medlemmer vises deltakelser i giveaways og gevinster.
    For bedriftsbrukere vises bedriftsinfo og giveaways-oversikt.
    """
    user = request.user
    context = {"user": user}

    # Sjekk om brukeren er en bedriftsbruker 
    if hasattr(user, 'business_account') and user.business_account:
        # Håndterer bedriftsbruker
        business = user.business_account
        try:
            giveaways = Giveaway.objects.filter(business=business)
            giveaways_active = giveaways.filter(is_active=True)
            giveaways_ended = giveaways.filter(is_active=False)
            giveaways_with_winner = giveaways.filter(winner__isnull=False)
            giveaways_log = giveaways.order_by('-created_at')[:10]
            
            # Omdirigerer til bedrifts-dashboard
            return HttpResponseRedirect(reverse('accounts:business_dashboard'))
        except Exception as e:
            logger.error(f"Feil ved lasting av bedriftsdashboard: {e}")
    else:
        # Håndterer vanlig medlem
        try:
            # Henter alle deltakelser for brukeren
            participations = Entry.objects.filter(user=user).select_related('giveaway').order_by('-created_at')
            
            # Teller antall gevinster
            wins = Winner.objects.filter(user=user).count()
            
            # Henter nylige giveaways for medlemmet
            recent_entries = participations[:5]
            
            context.update({
                'participations': participations,
                'recent_entries': recent_entries,
                'wins': wins,
            })
        except Exception as e:
            logger.error(f"Feil ved lasting av medlems-dashboard: {e}")
            messages.error(request, "Det oppsto en feil ved lasting av dashboardet. Vennligst prøv igjen senere.")
    
    return render(request, 'accounts/dashboard.html', context)

