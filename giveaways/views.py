from .permissions import can_enter_giveaway
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404
from django.utils.translation import gettext as _
from .models import Giveaway
from .forms import GiveawayCreateForm
from businesses.models import Business
import logging

logger = logging.getLogger(__name__)

# Admin task monitoring views and winner animation API

from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from celery.result import AsyncResult
from django.shortcuts import render

from .models import Giveaway, Winner


class GiveawayWinnerView(DetailView):
    """View for displaying the winner of a giveaway.
    
    This view shows the details of the winner for a completed giveaway.
    It displays the winner's information and the giveaway details.
    
    Attributes:
        model (Model): The Giveaway model class
        template_name (str): Path to the template for rendering the view
        context_object_name (str): Name of the giveaway object in the template context
    """
    model = Giveaway
    template_name = 'giveaways/giveaway_winner.html'
    context_object_name = 'giveaway'
    
    def get_context_data(self, **kwargs):
        """Get the context data for rendering the template.
        
        Adds winner information to the context if a winner exists.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            dict: The context dictionary with giveaway and winner information
        """
        context = super().get_context_data(**kwargs)
        giveaway = self.get_object()
        context['business'] = giveaway.business
        
        # Get winner information if available
        try:
            winner = Winner.objects.get(giveaway=giveaway)
            context['winner'] = winner
            # Get the winner's entry to show their answer
            winner_entry = winner.get_entry()
            if winner_entry:
                context['winner_entry'] = winner_entry
        except Winner.DoesNotExist:
            context['no_winner_yet'] = True
        
        # Include the total number of entries
        context['entries_count'] = giveaway.entry_count()
        
        # Check if the current user participated
        if self.request.user.is_authenticated:
            context['has_joined'] = giveaway.entries.filter(user=self.request.user).exists()
        
        return context


class GiveawayAnimationDataView(View):
    """
    API view that provides entry data for the winner selection animation.
    
    This endpoint returns a JSON array of entry data (first name, last name)
    for the specified giveaway. It only includes minimal required information
    for the animation and follows privacy best practices.
    """
    
    def get(self, request):
        giveaway_id = request.GET.get('giveaway_id')
        
        if not giveaway_id:
            return JsonResponse({
                "error": "Missing giveaway_id parameter",
                "message": "Please provide a giveaway_id parameter"
            }, status=400)
            
        try:
            # Get the giveaway
            giveaway = Giveaway.objects.get(id=giveaway_id)
            
            # Check if user has permission to view this giveaway
            if not self._can_view_giveaway(request.user, giveaway):
                return JsonResponse({
                    "error": "Permission denied",
                    "message": "You don't have permission to view this giveaway's entries"
                }, status=403)
            
            # Get entries for animation - limit fields to only what's needed
            entries = giveaway.entries.all().select_related('user')
            
            # Format entries for animation
            entry_data = [{
                "id": entry.id,
                "first_name": entry.user.first_name,
                "last_name": entry.user.last_name,
                # Include a partial (obfuscated) email for verification
                "email_hint": self._obfuscate_email(entry.user.email)
            } for entry in entries]
            
            return JsonResponse({
                "giveaway": {
                    "id": giveaway.id,
                    "title": giveaway.title
                },
                "entries": entry_data,
                "total_entries": len(entry_data)
            })
            
        except Giveaway.DoesNotExist:
            return JsonResponse({
                "error": "Giveaway not found",
                "message": f"No giveaway found with ID {giveaway_id}"
            }, status=404)
        except Exception as e:
            logger.exception(f"Error getting animation data: {str(e)}")
            return JsonResponse({
                "error": "Server error",
                "message": "An error occurred while retrieving animation data"
            }, status=500)
    
    def _can_view_giveaway(self, user, giveaway):
        """Check if user can view this giveaway's entries."""
        # Business owners can view their own giveaways
        if user.is_authenticated and hasattr(user, 'business_profile'):
            return user.business_profile.business == giveaway.business
        
        # Staff/admin can view any giveaway
        return user.is_staff or user.is_superuser
    
    def _obfuscate_email(self, email):
        """Create a privacy-friendly version of the email."""
        parts = email.split('@')
        if len(parts) != 2:
            return "***"
            
        username, domain = parts
        if len(username) <= 2:
            return f"{username[0]}***@{domain[0]}***"
            
        return f"{username[0:2]}***@{domain[0:2]}***"


class WinnerAnimationView(DetailView):
    """
    View that displays the arcade claw machine animation for a giveaway winner.
    
    This view renders a template with the claw machine animation that visually
    demonstrates the random selection process for a giveaway winner.
    """
    model = Giveaway
    template_name = 'giveaways/giveaway_winner_animation.html'
    context_object_name = 'giveaway'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        giveaway = self.get_object()
        
        # Check if this giveaway has a winner
        try:
            winner = Winner.objects.get(giveaway=giveaway)
            context['winner'] = winner
            # Get the winner's entry to show their answer
            winner_entry = winner.get_entry()
            if winner_entry:
                context['winner_entry'] = winner_entry
            
            # Get all entries for the animation
            entries = giveaway.entries.all().select_related('user')
            context['entries'] = entries
            context['entries_count'] = entries.count()
            
        except Winner.DoesNotExist:
            context['no_winner_yet'] = True
        
        # Add business info
        context['business'] = giveaway.business
        
        return context


class WinnerSelectionStatusView(View):
    """
    Admin view for checking the status of winner selection tasks.
    
    Provides a JSON API for monitoring long-running winner selection tasks.
    This view is only accessible to staff members.
    """
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        task_id = request.GET.get('task_id')
        
        if not task_id:
            return JsonResponse({
                "error": "No task ID provided",
                "message": "Please provide a task_id parameter"
            }, status=400)
            
        # Get the task result
        result = AsyncResult(task_id)
        
        # Prepare response data
        data = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "timestamp": str(timezone.now())
        }
        
        # Add result data if available
        if result.ready():
            if result.successful():
                # Get the actual result data
                result_data = result.result
                
                # Include only safe data (not exposing any sensitive information)
                safe_data = {
                    "total_processed": result_data.get("total_processed", 0),
                    "winners_selected": result_data.get("winners_selected", 0),
                    "errors": result_data.get("errors", 0),
                    "completed_at": result_data.get("completed_at", ""),
                    "chunks_processed": result_data.get("chunks_processed", 0)
                }
                
                # Add summary messages if available (limited to prevent large responses)
                if "summary_messages" in result_data:
                    safe_data["summary_messages"] = result_data["summary_messages"][:10]
                    safe_data["has_more_messages"] = len(result_data.get("summary_messages", [])) > 10
                
                data["result"] = safe_data
            else:
                # Include error information
                data["error"] = str(result.result)
        
        return JsonResponse(data)

class GiveawayListView(ListView):
    """
    Public overview of active giveaways with advanced filtering options.
    
    Features:
    - Location-based filtering (city, postal code)
    - Status filtering (active, upcoming, all)
    - Optimized database queries
    - Accessibility enhancements
    - Responsive pagination
    """
    model = Giveaway
    template_name = "giveaways/giveaway_list.html"
    context_object_name = "giveaways"
    paginate_by = 12

    def get_queryset(self):
        """
        Build an optimized queryset with all necessary filters applied.
        Uses select_related to minimize database queries.
        """
        # Start with base queryset - only consider active giveaways
        queryset = Giveaway.objects.filter(is_active=True)
        
        # Date filtering
        show_all_dates = self.request.GET.get("all_dates")
        if not show_all_dates:
            from django.utils import timezone
            now = timezone.now()
            queryset = queryset.filter(start_date__lte=now, end_date__gte=now)
            
        # Location filtering
        city = self.request.GET.get("city")
        postal_code = self.request.GET.get("postal_code")
        
        # Case-insensitive city matching with normalization
        if city:
            from .services import normalize_city_name
            normalized_city = normalize_city_name(city)
            queryset = queryset.filter(business__city__iexact=normalized_city)
            
        if postal_code:
            queryset = queryset.filter(business__postal_code=postal_code)
            
        # Category filtering
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)
            
        # Sorting
        sort_by = self.request.GET.get("sort", "end_date")
        valid_sort_fields = ['end_date', '-end_date', 'start_date', '-start_date', 
                            'title', '-title']
                            
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            # Default sort - ending soon first
            queryset = queryset.order_by("end_date")
        
        # Optimize database access with select_related
        return queryset.select_related("business")

    def get_context_data(self, **kwargs):
        """
        Add filter context, statistics and accessibility enhancements.
        """
        context = super().get_context_data(**kwargs)
        
        # Filter values for form state preservation
        context["selected_city"] = self.request.GET.get("city", "")
        context["selected_postal_code"] = self.request.GET.get("postal_code", "")
        context["all_dates"] = self.request.GET.get("all_dates", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_sort"] = self.request.GET.get("sort", "end_date")
        
        # Get cities with active giveaways for dropdown
        from django.db.models import Count
        cities = Giveaway.objects.filter(is_active=True)\
            .values('business__city')\
            .annotate(count=Count('id'))\
            .filter(count__gt=0)\
            .order_by('business__city')
            
        context["available_cities"] = cities
        
        # Add statistics for template
        from django.utils import timezone
        now = timezone.now()
        
        # Provide count of active, upcoming and total giveaways
        from django.db.models import Q
        giveaway_stats = Giveaway.objects.filter(is_active=True).aggregate(
            active_count=Count('id', filter=Q(start_date__lte=now, end_date__gte=now)),
            upcoming_count=Count('id', filter=Q(start_date__gt=now)),
            total=Count('id')
        )
        
        context["giveaway_stats"] = giveaway_stats
        
        # Get categories for filtering
        categories = Giveaway.objects.values_list('category', flat=True)\
            .distinct().order_by('category')
        context["categories"] = [c for c in categories if c]  # Filter out empty categories
        
        # Add accessibility enhancements
        context["accessibility"] = {
            "aria_labels": {
                "giveaway_list": _('Liste over aktive giveaways'),
                "filter_form": _('Filter giveaways etter sted og kategori'),
                "pagination": _('Sidenavigasjon for giveaway-liste')
            },
            "help_text": {
                "city": _('Velg by for å se giveaways i nærheten av deg'),
                "postal_code": _('Skriv inn postnummer for å finne giveaways'),
                "all_dates": _('Vis også kommende giveaways som ikke har startet ennå')
            }
        }
        
        return context


from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import EntryForm

from .models import Giveaway

class GiveawayDetailView(DetailView):
    """
    Detailed view of a giveaway with entry form for members.
    
    Handles:
    1. Displaying giveaway details and business info
    2. Showing entry form for eligible members
    3. Processing form submissions for participation
    4. Validating user eligibility based on location and membership
    """
    model = Giveaway
    template_name = 'giveaways/giveaway_detail.html'
    context_object_name = 'giveaway'
    
    def get_object(self, queryset=None):
        """
        Retrieve the giveaway with all related objects for better performance.
        """
        if queryset is None:
            queryset = self.get_queryset()
            
        # Use select_related to reduce database queries
        queryset = queryset.select_related('business')
        
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)
            
        try:
            obj = queryset.get()
            return obj
        except queryset.model.DoesNotExist:
            raise Http404(_("Ingen giveaway funnet med denne ID-en"))
    
    def get_entry_form_kwargs(self, post=False):
        """
        Prepare form kwargs with giveaway and request objects.
        """
        kwargs = {'giveaway': self.get_object(), 'request': self.request}
        if post:
            kwargs['data'] = self.request.POST
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Add giveaway, business, participation status and form to context.
        """
        context = super().get_context_data(**kwargs)
        giveaway = self.get_object()
        user = self.request.user
        
        # Use cached property pattern for expensive queries
        entries_count = getattr(self, '_entries_count', None)
        if entries_count is None:
            entries_count = giveaway.entries.count()
            self._entries_count = entries_count
        
        # Import is_member function
        from .permissions import is_member
        
        # Check various user statuses
        is_member_status = is_member(user) if user.is_authenticated else False
        is_business_user = hasattr(user, "business_account") if user.is_authenticated else False
        
        # Check participation eligibility
        has_joined = False
        if user.is_authenticated:
            has_joined = giveaway.entries.filter(user=user).exists()
            
        can_participate = can_enter_giveaway(user, giveaway)
        
        # Get participation status text for better user feedback
        participation_status = self._get_participation_status(
            user, giveaway, is_member_status, has_joined, can_participate
        )
        
        # Only create entry form if user can participate
        entry_form = None
        if can_participate:
            entry_form = EntryForm(**self.get_entry_form_kwargs())
        
        # Get related business with all needed fields
        business = giveaway.business
        
        # Add accessibility enhancements
        accessibility = {
            "aria_labels": {
                "entry_form": _('Skjema for påmelding til giveaway'),
                "business_info": _('Informasjon om bedriften'),
                "giveaway_details": _('Detaljer om giveawayen'),
            },
            "has_form": entry_form is not None,
        }
        
        # Build comprehensive context for template
        context.update({
            "business": business,
            "entries_count": entries_count,
            "is_member": is_member_status,
            "is_business": is_business_user,
            "has_joined": has_joined,
            "can_participate": can_participate,
            "entry_form": entry_form,
            "participation_status": participation_status,
            "accessibility": accessibility,
            "is_active_giveaway": giveaway.is_currently_active(),
        })
        return context
        
    def _get_participation_status(self, user, giveaway, is_member, has_joined, can_participate):
        """
        Generate user-friendly participation status message.
        """
        if not user.is_authenticated:
            return {
                "message": _('Du må være innlogget for å delta'),
                "status": "info",
                "icon": "info-circle"
            }
        elif not is_member:
            return {
                "message": _('Kun medlemmer kan delta i giveaways'),
                "status": "warning",
                "icon": "exclamation-triangle"
            }
        elif has_joined:
            return {
                "message": _('Du er allerede påmeldt denne giveawayen'),
                "status": "success",
                "icon": "check-circle"
            }
        elif not giveaway.is_currently_active():
            if giveaway.is_upcoming():
                return {
                    "message": _('Denne giveawayen har ikke startet ennå'),
                    "status": "info",
                    "icon": "clock"
                }
            else:
                return {
                    "message": _('Denne giveawayen er avsluttet'),
                    "status": "secondary",
                    "icon": "calendar-check"
                }
        elif can_participate:
            return {
                "message": _('Du kan delta i denne giveawayen!'),
                "status": "primary",
                "icon": "gift"
            }
        else:
            return {
                "message": _('Du kan ikke delta i denne giveawayen'),
                "status": "danger",
                "icon": "ban"
            }

    def post(self, request, *args, **kwargs):
        """
        Handle entry form submission with comprehensive validation.
        """
        self.object = self.get_object()
        user = request.user
        
        # Security check - verify user can participate
        if not can_enter_giveaway(user, self.object):
            messages.error(
                request, 
                _('Du har ikke tilgang til å delta i denne giveawayen.')
            )
            logger.warning(
                f"Ugyldig påmeldingsforsøk: {user.email} for giveaway {self.object.id}"
            )
            return redirect(self.object.get_absolute_url())

        # Process form submission with robust error handling
        form = EntryForm(**self.get_entry_form_kwargs(post=True))
        
        # Critical fix: Pre-validate to check for errors before is_valid call
        # This prevents RelatedObjectDoesNotExist errors
        try:
            if form.is_valid():
                try:
                    # Create entry instance but don't save to db yet
                    entry = form.save(commit=False)
                    # Set both required foreign keys
                    entry.user = user
                    entry.giveaway = self.object
                    
                    # Final validation check before saving
                    # This validates the full model with all fields set
                    entry.full_clean()
                    
                    # Now save the entry to the database
                    entry.save()
                    
                    # Success message with toast notification
                    messages.success(
                        request, 
                        _('Du er nå påmeldt! Lykke til i trekningen.')
                    )
                    
                    # Log successful entry
                    logger.info(
                        f"Bruker {user.email} meldte seg på giveaway {self.object.id} "
                        f"fra {entry.user_location_city}."
                    )
                    
                    return redirect(self.object.get_absolute_url())
                except ValidationError as ve:
                    # Handle validation errors
                    logger.warning(f"Valideringsfeil ved påmelding: {str(ve)}")
                    for field, errors in ve.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                except IntegrityError:
                    # Handle unique constraint violations (user already entered)
                    logger.warning(f"Bruker {user.email} har allerede meldt seg på giveaway {self.object.id}")
                    messages.error(
                        request,
                        _('Du har allerede meldt deg på denne giveawayen.')
                    )
                    return redirect(self.object.get_absolute_url())
                except Exception as e:
                    # Handle other unexpected errors
                    logger.error(f"Feil ved lagring av påmelding: {str(e)}")
                    messages.error(
                        request, 
                        _('Det oppstod en feil ved påmelding. Vennligst prøv igjen.')
                    )
        except Exception as form_error:
            # Catch any exceptions during form validation
            logger.error(f"Feil ved validering av skjema: {str(form_error)}")
            messages.error(
                request,
                _('Det oppstod en feil ved validering av skjemaet. Vennligst prøv igjen.')
            )
        else:
            # Form validation failed
            logger.warning(
                f"Påmelding mislyktes for {user.email} til giveaway {self.object.id}: "
                f"{form.errors}"
            )
            
        # Re-render form with errors
        context = self.get_context_data()
        context["entry_form"] = form
        return self.render_to_response(context)


class BusinessContextMixin:
    """
    Mixin providing common functionality for business-related views.
    Includes methods for retrieving business data and stats.
    """
    def get_business(self):
        """
        Retrieves the business object for the logged-in user with efficient caching.
        """
        if not hasattr(self, '_business_cache'):
            user = self.request.user
            self._business_cache = getattr(user, 'business_account', None)
        return self._business_cache
        
    def get_business_stats(self):
        """
        Calculates statistics for a business: giveaways, participants, winners.
        Uses efficient queries with aggregation instead of multiple queries.
        """
        business = self.get_business()
        if not business:
            return {}
            
        # Import models here to avoid circular imports
        from .models import Giveaway, Entry, Winner
        
        # Use efficient aggregation queries
        giveaways = Giveaway.objects.filter(business=business)
        giveaways_active = giveaways.filter(is_active=True)
        giveaways_ended = giveaways.filter(is_active=False)
        
        # Calculate statistics with annotation and aggregation
        from django.db.models import Count, Q
        from django.utils import timezone
        now = timezone.now()
        
        giveaway_stats = giveaways.aggregate(
            total=Count('id'),
            active_count=Count('id', filter=Q(is_active=True)),
            current_count=Count('id', filter=Q(is_active=True, start_date__lte=now, end_date__gte=now)),
            upcoming_count=Count('id', filter=Q(is_active=True, start_date__gt=now)),
            ended_count=Count('id', filter=Q(is_active=False) | Q(end_date__lt=now))
        )
        
        entry_stats = Entry.objects.filter(giveaway__business=business).aggregate(
            total_participants=Count('id'),
            unique_participants=Count('user', distinct=True)
        )
        
        winner_stats = Winner.objects.filter(giveaway__business=business).aggregate(
            total_winners=Count('id')
        )
        
        # Recent activities with efficient queries
        recent_giveaways = giveaways.order_by('-created_at')[:5]
        recent_winners = Winner.objects.filter(
            giveaway__business=business
        ).select_related('user', 'giveaway').order_by('-selected_at')[:5]
        
        return {
            **giveaway_stats,
            **entry_stats,
            **winner_stats,
            "recent_giveaways": recent_giveaways,
            "recent_winners": recent_winners,
        }

class BusinessOnlyMixin(UserPassesTestMixin):
    """
    Mixin som kun tillater bedriftsbrukere tilgang.
    Provides secure role-based access control for business functionality.
    """
    def test_func(self):
        """
        Verify the user is authenticated and has a business account.
        """
        user = self.request.user
        has_business = user.is_authenticated and hasattr(user, "business_account")
        
        # Log unauthorized access attempts
        if user.is_authenticated and not has_business:
            logger.warning(f"Non-business user {user.email} attempted to access business-only view")
            
        return has_business

    def handle_no_permission(self):
        """
        Provide helpful feedback when access is denied.
        """
        from django.contrib import messages
        messages.error(
            self.request, 
            _("Kun bedriftsbrukere kan opprette giveaways. Logg inn med en bedriftskonto.")
        )
        return redirect("accounts:member-profile")

class GiveawayCreateView(LoginRequiredMixin, BusinessOnlyMixin, BusinessContextMixin, CreateView):
    """
    View for å opprette en giveaway for innlogget bedriftsbruker.
    
    Features:
    - Automatic business association for the created giveaway
    - Form validation with helpful error messages
    - Business context data for the template
    - Accessibility enhancements
    """
    model = Giveaway
    form_class = GiveawayCreateForm
    template_name = "giveaways/giveaway_form.html"
    success_url = reverse_lazy('giveaways:business-giveaways')
    
    def get_form_kwargs(self):
        """
        Pass the current user's business to the form for validation.
        """
        kwargs = super().get_form_kwargs()
        kwargs['business'] = self.get_business()
        return kwargs
    
    def get_context_data(self, **kwargs):
        """
        Add business info and accessibility context to the template.
        """
        context = super().get_context_data(**kwargs)
        business = self.get_business()
        
        # Add business context
        context['business'] = business
        context['business_stats'] = self.get_business_stats()
        
        # Add accessibility enhancements
        context['accessibility'] = {
            "aria_labels": {
                "form": _('Skjema for å opprette ny giveaway'),
                "business_section": _('Din bedriftsinformasjon'),
                "instructions": _('Instruksjoner for giveaway-oppretting')
            }
        }
        
        # Add form help text and instructions
        context['instructions'] = {
            "title": _('Tips for å lage en vellykket giveaway:'),
            "tips": [
                _('Velg en kort og fengende tittel'),
                _('Skriv en tydelig beskrivelse av premien'),
                _('Lag et spørsmål som er relevant for din bedrift'),
                _('Sett en rimelig tidsramme (anbefalt: 1-2 uker)'),
                _('Spesifiser målgruppen gjennom lokasjonskrav')
            ]
        }
        
        return context
        
    def form_valid(self, form):
        """
        Automatically assign the current user's business to the giveaway.
        """
        try:
            # Get the business account for the current user
            business = self.get_business()
            if not business:
                form.add_error(None, _('Du må ha en tilknyttet bedriftskonto for å opprette giveaways'))
                return self.form_invalid(form)
            
            # Set the business before saving
            form.instance.business = business
            
            # Log the creation
            response = super().form_valid(form)
            logger.info(f"Giveaway opprettet: {form.instance.title} av {business.name}")
            
            # Add success message
            messages.success(
                self.request,
                _('Giveaway opprettet! Den er nå synlig for kvalifiserte medlemmer.')
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Feil ved oppretting av giveaway: {str(e)}")
            form.add_error(None, _('Det oppstod en feil ved oppretting av giveaway. Vennligst prøv igjen.'))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Log validation errors and provide helpful feedback.
        """
        user = self.request.user
        logger.warning(f"Ugyldig giveaway-skjema fra {user.email}: {form.errors}")
        
        messages.error(
            self.request,
            _('Vennligst rett feilene i skjemaet og prøv igjen.')
        )
        
        return super().form_invalid(form)

class GiveawayEditView(LoginRequiredMixin, BusinessOnlyMixin, BusinessContextMixin, UpdateView):
    """
    View for redigering av eksisterende giveaway.
    
    Features:
    - Automatic business validation (ensure user can only edit own giveaways)
    - Form validation with helpful error messages
    - Preserves original creation data
    - Accessibility enhancements
    """
    model = Giveaway
    form_class = GiveawayCreateForm
    template_name = "giveaways/giveaway_form.html"
    context_object_name = "giveaway"
    
    def get_queryset(self):
        """
        Filter queryset to only allow editing of giveaways owned by the current business.
        """
        business = self.get_business()
        return Giveaway.objects.filter(business=business)
    
    def get_form_kwargs(self):
        """
        Pass the current user's business to the form for validation.
        """
        kwargs = super().get_form_kwargs()
        kwargs['business'] = self.get_business()
        return kwargs
    
    def get_context_data(self, **kwargs):
        """
        Add business info, edit mode flag, and accessibility context to the template.
        """
        context = super().get_context_data(**kwargs)
        business = self.get_business()
        
        # Add business context
        context['business'] = business
        context['business_stats'] = self.get_business_stats()
        context['edit_mode'] = True
        
        # Add accessibility enhancements
        context['accessibility'] = {
            "aria_labels": {
                "form": _('Skjema for å redigere giveaway'),
                "business_section": _('Din bedriftsinformasjon'),
                "instructions": _('Instruksjoner for giveaway-redigering')
            }
        }
        
        return context
        
    def form_valid(self, form):
        """
        Validate ownership and handle the edit properly.
        """
        try:
            # Get the business account for the current user
            business = self.get_business()
            if not business:
                form.add_error(None, _('Du må ha en tilknyttet bedriftskonto for å redigere giveaways'))
                return self.form_invalid(form)
            
            # Verify this giveaway belongs to the business
            if form.instance.business != business:
                form.add_error(None, _('Du kan bare redigere dine egne giveaways'))
                return self.form_invalid(form)
            
            # Log the update
            response = super().form_valid(form)
            logger.info(f"Giveaway redigert: {form.instance.title} av {business.name}")
            
            # Add success message
            messages.success(
                self.request,
                _('Giveaway oppdatert!')
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Feil ved redigering av giveaway: {str(e)}")
            form.add_error(None, _('Det oppstod en feil ved redigering av giveaway. Vennligst prøv igjen.'))
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """
        Log validation errors and provide helpful feedback.
        """
        user = self.request.user
        logger.warning(f"Ugyldig giveaway-redigeringsskjema fra {user.email}: {form.errors}")
        
        messages.error(
            self.request,
            _('Vennligst rett feilene i skjemaet og prøv igjen.')
        )
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('giveaways:business-giveaways')


class BusinessGiveawayListView(LoginRequiredMixin, BusinessOnlyMixin, BusinessContextMixin, ListView):
    """
    View for å vise en liste over giveaways for innlogget bedriftsbruker.
    
    Features:
    - Automatic business association for the listed giveaways
    - Filtering and sorting of giveaways
    - Status statistics and performance overview
    - Accessibility enhancements
    """
    model = Giveaway
    template_name = "giveaways/business_giveaway_list.html"
    context_object_name = "giveaways"
    paginate_by = 10
    
    def get_queryset(self):
        """
        Filter giveaways by the current user's business with efficient querying.
        """
        business = self.get_business()
        if not business:
            return Giveaway.objects.none()
        
        # Get optional filters from request
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', '-created_at')  # Default: newest first
        
        # Start with business-filtered queryset
        queryset = Giveaway.objects.filter(business=business)
        
        # Apply status filter if provided
        from django.utils import timezone
        now = timezone.now()
        
        if status_filter == 'active':
            queryset = queryset.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            )
        elif status_filter == 'upcoming':
            queryset = queryset.filter(
                is_active=True,
                start_date__gt=now
            )
        elif status_filter == 'ended':
            queryset = queryset.filter(
                is_active=False
            ) | queryset.filter(
                end_date__lt=now
            )
        
        # Apply sorting
        valid_sort_fields = ['title', '-title', 'start_date', '-start_date', 
                            'end_date', '-end_date', 'created_at', '-created_at',
                            'participants', '-participants']
        
        if sort_by == 'participants' or sort_by == '-participants':
            # Need to annotate for participant count sorting
            from django.db.models import Count
            queryset = queryset.annotate(participants_count=Count('entries'))
            if sort_by == 'participants':
                queryset = queryset.order_by('participants_count')
            else:
                queryset = queryset.order_by('-participants_count')
        elif sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            # Default sort
            queryset = queryset.order_by('-created_at')
            
        # Use select_related for business to optimize queries
        return queryset.select_related('business')
    
    def get_context_data(self, **kwargs):
        """
        Add business info, statistics and accessibility context to the template.
        """
        context = super().get_context_data(**kwargs)
        business = self.get_business()
        
        # Current filtering and sorting options for template
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        
        # Add business context
        context['business'] = business
        context['business_stats'] = self.get_business_stats()
        
        # Add summary statistics for quick view
        from django.utils import timezone
        now = timezone.now()
        from django.db.models import Count, Q
        
        all_giveaways = Giveaway.objects.filter(business=business)
        status_counts = all_giveaways.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True, start_date__lte=now, end_date__gte=now)),
            upcoming=Count('id', filter=Q(is_active=True, start_date__gt=now)),
            ended=Count('id', filter=Q(is_active=False) | Q(end_date__lt=now))
        )
        
        context['status_counts'] = status_counts
        
        # Add accessibility enhancements
        context['accessibility'] = {
            "aria_labels": {
                "list": _('Liste over dine giveaways'),
                "filter": _('Filtrer giveaways etter status'),
                "sort": _('Sorter giveaways etter egenskaper')
            }
        }
        
        return context