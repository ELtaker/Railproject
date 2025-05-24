import logging
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST
import json
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

# Views are organized following Django best practices with CBVs for complex views

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
    
    This view displays the member profile for logged-in users.
    Requires authentication and uses the member_profile.html template.
    """
    template_name = "accounts/member_profile.html"
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
    template_name = "accounts/member_profile_edit.html"
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
    login_url = "accounts:business-login"
    

@require_POST
@login_required
def update_location(request):
    """
    AJAX endpoint to update a user's location based on browser geolocation.
    
    This function handles the update of user location from geolocation API requests.  
    It expects a JSON payload with a 'city' field and returns a JSON response.
    
    Args:
        request: HttpRequest object with JSON body
    Returns:
        JsonResponse with success/error information
    """
    from django.utils.html import strip_tags
    from django.views.decorators.csrf import csrf_protect
    
    try:
        # Parse the JSON data from the request body
        data = json.loads(request.body)
        city = data.get('city')
        
        # Validate input
        if not city:
            return JsonResponse({'success': False, 'error': 'By er påkrevd'}, status=400)
        
        if len(city) > 100:
            return JsonResponse({'success': False, 'error': 'Bynavn er for langt'}, status=400)
            
        # Sanitize input to prevent XSS
        city = strip_tags(city)
        
        # Validate city format (no numbers allowed)
        import re
        if re.search(r'[0-9]', city):
            return JsonResponse({'success': False, 'error': 'Bynavn kan ikke inneholde tall'}, status=400)
        
        # Update the user's city in their profile
        user = request.user
        user.city = city
        user.save()
        
        # Also update MemberProfile if it exists
        if hasattr(user, 'member_profile'):
            profile = user.member_profile
            profile.city = city
            profile.save()
        
        logger.info(f"User location updated via geolocation: {user.username} -> {city}")
        
        return JsonResponse({
            'success': True,
            'message': 'Lokasjon oppdatert',
            'city': city
        })
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in update_location from user {request.user.username}")
        return JsonResponse({'success': False, 'error': 'Ugyldig JSON-format'}, status=400)
    except Exception as e:
        logger.error(f"Error updating user location for {request.user.username}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Server feil'}, status=500)

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

from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator

# Function-based view with explicit CSRF handling for member registration
@ensure_csrf_cookie
@csrf_protect
def member_register_view(request):
    """
    Function-based view for registering new members on Raildrops.
    Shows registration form, validates input, and creates new user.
    Includes explicit CSRF handling with ensure_csrf_cookie and csrf_protect decorators.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            from django.contrib.auth.models import Group
            # Save user without committing to get the user instance
            user = form.save(commit=False)
            # Save the city from the form to the User model
            user.city = form.cleaned_data.get('city', '')
            # Now save the user with the city field
            user.save()
            
            # Create MemberProfile with city
            from .models import MemberProfile
            MemberProfile.objects.create(
                user=user,
                city=form.cleaned_data.get('city', '')
            )
            
            # Add user to Medlem group
            medlem_group, _ = Group.objects.get_or_create(name="Medlem")
            user.groups.add(medlem_group)
            
            # Specify backend for regular users
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f"User registered: {user.username} ({user.email}) from {user.city}")
            messages.success(request, "User registered and logged in!")
            return redirect('accounts:dashboard')
    else:
        form = UserRegistrationForm()
    
    # Add ARIA attributes to form fields for better accessibility
    if hasattr(form, 'fields'):
        for field in form.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({
                    'class': 'form-control',
                    'aria-required': 'true' if field.required else 'false'
                })
    
    return render(request, 'accounts/member_register.html', {
        'form': form,
    })

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
    """
    Håndterer utlogging for alle brukertyper.
    Logger ut brukeren og viser en suksessmelding.
    
    Args:
        request: HttpRequest object
    Returns:
        HttpResponseRedirect til hjemmesiden
    """
    logout(request)
    messages.success(request, "Du er nå logget ut.")
    return redirect('home')

@login_required
def dashboard_view(request):
    """
    Viser dashboard for innlogget bruker. 
    For vanlige medlemmer vises deltakelser i giveaways og gevinster.
    For bedriftsbrukere vises bedriftsinfo og giveaways-oversikt.
    
    Args:
        request: HttpRequest object
    Returns:
        HttpResponse with dashboard content based on user role
    """
    user = request.user
    context = {"user": user}

    # Sjekk om brukeren er en bedriftsbruker 
    if hasattr(user, 'business_account') and user.business_account:
        # Omdirigerer til bedrifts-dashboard direkte (handled by businesses app)
        return HttpResponseRedirect(reverse('businesses:business-dashboard'))
    else:
        # Håndterer vanlig medlem
        try:
            # Use select_related to reduce database queries
            participations = Entry.objects.filter(user=user)\
                .select_related('giveaway', 'giveaway__business')\
                .order_by('-entered_at')
            
            # Get nearby giveaways if user has location
            nearby_giveaways = []
            if user.city:
                nearby_giveaways = Giveaway.objects.filter(
                    business__city=user.city,
                    is_active=True
                ).select_related('business')[:5]
            
            # Teller antall gevinster - bruk select_related for å redusere spørringer
            wins = Winner.objects.filter(user=user).select_related('giveaway').count()
            
            context.update({
                'participations': participations,
                'recent_entries': participations[:5],
                'wins': wins,
                'nearby_giveaways': nearby_giveaways,
            })
        except Exception as e:
            logger.error(f"Error loading member dashboard: {str(e)}")
            messages.error(request, "Det oppsto en feil ved lasting av dashboardet. Vennligst prøv igjen senere.")
    
    return render(request, 'accounts/member_dashboard.html', context)

