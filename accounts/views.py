import logging
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from .forms import UserRegistrationForm, UserProfileForm, BusinessRegistrationForm, MemberLoginForm, CompanyRegistrationForm, CompanyLoginForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Company
from .backends import CompanyAuthBackend
from django.contrib.auth import get_user_model
User = get_user_model()

logger = logging.getLogger(__name__)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from giveaways.models import Entry, Winner, Giveaway
from .permissions import user_is_member, user_is_business
from .forms import BusinessProfileForm
from businesses.models import Business

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
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
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
    success_url = reverse_lazy("profile")
    login_url = "login"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        logger.info(f"Profil oppdatert for bruker: {self.request.user.username}")
        messages.success(self.request, "Profilen din er oppdatert!")
        return super().form_valid(form)

    """
    Viser medlemsprofil for innloggede brukere.
    Krever innlogging.
    """
    template_name = "accounts/profile.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        logger.info(f"Profilside vist for bruker: {self.request.user.username}")
        return context

class BusinessRegisterView(FormView):
    """
    View for registrering av bedriftsbrukere og tilknyttet bedrift på Raildrops.
    Viser skjema, validerer input og oppretter både bruker og Business.
    """
    template_name = "accounts/business_register.html"
    form_class = BusinessRegistrationForm
    success_url = reverse_lazy("login")

    def form_valid(self, form: BusinessRegistrationForm):
        user = form.save()
        logger.info(f"Bedriftsbruker registrert: {user.username} ({user.email})")
        messages.success(self.request, "Bedriftskonto registrert! Du kan nå logge inn.")
        return super().form_valid(form)

class UserRegisterView(FormView):
    """
    View for registrering av nye medlemmer på Raildrops.
    Viser registreringsskjema, validerer input og oppretter ny bruker.
    """
    template_name = "accounts/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("accounts:member_login")

    def form_valid(self, form: UserRegistrationForm):
        user = form.save()
        # Spesifiser backend for vanlige brukere
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        logger.info(f"Bruker registrert: {user.username} ({user.email})")
        messages.success(self.request, "Bruker registrert og innlogget!")
        return redirect('accounts:dashboard')


def member_login_view(request):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"POST data: {request.POST}")
    # Prøv å logge CSRF-token fra POST og fra context
    csrf_token_post = request.POST.get('csrfmiddlewaretoken', None)
    logger.info(f"CSRF token fra POST: {csrf_token_post}")
    if request.method == 'POST':
        form = MemberLoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data['user'])
            messages.success(request, "Du er nå logget inn som medlem.")
            return redirect('accounts:dashboard')
    else:
        form = MemberLoginForm()
    # Legg csrf_token eksplisitt i context for feilsøking
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)
    logger.info(f"CSRF token fra get_token: {csrf_token}")
    return render(request, 'accounts/member_login.html', {'form': form, 'csrf_token': csrf_token})

class CompanyRegisterView(FormView):
    template_name = "accounts/company_register.html"
    form_class = CompanyRegistrationForm
    success_url = reverse_lazy("accounts:company_login")

    def form_valid(self, form):
        company = form.save()
        login(self.request, company, backend='accounts.backends.CompanyAuthBackend')
        messages.success(self.request, "Bedrift registrert og innlogget!")
        return redirect('accounts:dashboard')

def company_login_view(request):
    if request.method == 'POST':
        form = CompanyLoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data['company'], backend='accounts.backends.CompanyAuthBackend')
            messages.success(request, "Du er nå logget inn som bedrift.")
            return redirect('accounts:dashboard')
    else:
        form = CompanyLoginForm()
    return render(request, 'accounts/company_login.html', {'form': form})

def custom_logout_view(request):
    logout(request)
    messages.success(request, "Du er nå logget ut.")
    return redirect('home')

class BusinessProfileEditView(LoginRequiredMixin, UpdateView):
    model = Business
    form_class = BusinessProfileForm
    template_name = "accounts/business_profile_edit.html"
    success_url = "/accounts/dashboard/"
    login_url = "accounts:company_login"

    def get_object(self, queryset=None):
        # Finn Business-profil for innlogget Company-bruker
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
    Viser dashboard for innlogget bedrift med giveaways-oversikt og bedriftsinfo.
    """
    user = request.user
    is_company = hasattr(user, 'company_name') or hasattr(user, 'organization_number')
    context = {"user": user, "is_company": is_company, "is_member": user_is_member(user), "is_business": user_is_business(user)}

    if is_company:
        # Finn Business hvor bruker er admin
        try:
            business = Business.objects.get(admin=user)
            giveaways = Giveaway.objects.filter(business=business)
            giveaways_active = giveaways.filter(is_active=True)
            giveaways_ended = giveaways.filter(is_active=False)
            giveaways_with_winner = giveaways.filter(winner__isnull=False)
            giveaways_log = giveaways.order_by('-created_at')[:10]  # Siste 10 hendelser
        except Business.DoesNotExist:
            business = None
            giveaways_active = []
            giveaways_ended = []
            giveaways_with_winner = []
            giveaways_log = []
        context.update({
            'company': user,
            'business': business,
            'giveaways_active': giveaways_active,
            'giveaways_ended': giveaways_ended,
            'giveaways_with_winner': giveaways_with_winner,
            'giveaways_log': giveaways_log,
        })
    return render(request, 'accounts/dashboard.html', context)

