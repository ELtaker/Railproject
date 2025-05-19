from .permissions import can_enter_giveaway
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import CreateView
from .models import Giveaway
from .forms import GiveawayCreateForm
from businesses.models import Business
import logging

logger = logging.getLogger(__name__)

from django.views.generic import ListView, DetailView

class GiveawayListView(ListView):
    """
    Public overview of active giveaways. Can be filtered by location/postal code.
    Shows only active giveaways (currently between start and end dates).
    """
    model = Giveaway
    template_name = "giveaways/giveaway_list.html"
    context_object_name = "giveaways"
    paginate_by = 12

    def get_queryset(self):
        qs = Giveaway.objects.filter(is_active=True)
        now = self.request.GET.get("all_dates")
        if not now:
            from django.utils import timezone
            now = timezone.now()
            qs = qs.filter(start_date__lte=now, end_date__gte=now)
        city = self.request.GET.get("city")
        postal_code = self.request.GET.get("postal_code")
        if city:
            qs = qs.filter(business__city__iexact=city)
        if postal_code:
            qs = qs.filter(business__postal_code=postal_code)
        qs = qs.select_related("business").order_by("end_date")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_city"] = self.request.GET.get("city", "")
        context["selected_postal_code"] = self.request.GET.get("postal_code", "")
        context["all_dates"] = self.request.GET.get("all_dates", "")
        return context


from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import EntryForm

from .models import Giveaway

class GiveawayDetailView(DetailView):
    model = Giveaway
    def get_entry_form_kwargs(self, post=False):
        kwargs = {'giveaway': self.get_object(), 'request': self.request}
        if post:
            kwargs['data'] = self.request.POST
        # Remove custom kwargs before sending to ModelForm
        form_kwargs = {}
        if 'data' in kwargs:
            form_kwargs['data'] = kwargs['data']
        if 'files' in kwargs:
            form_kwargs['files'] = kwargs['files']
        # These are only used in our __init__
        form_kwargs['giveaway'] = kwargs['giveaway']
        form_kwargs['request'] = kwargs['request']
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        giveaway = self.get_object()
        user = self.request.user
        entries_count = giveaway.entries.count()
        
        # Import is_member function that we fixed earlier
        from .permissions import is_member
        
        # Check if user is a member
        is_member_status = is_member(user) if user.is_authenticated else False
        
        # Check if user has already joined this giveaway
        has_joined = False
        if user.is_authenticated:
            has_joined = giveaway.entries.filter(user=user).exists()
            
        # Check if user can participate
        can_participate = can_enter_giveaway(user, giveaway)
        
        # Only create entry form if user can participate
        entry_form = EntryForm(giveaway=giveaway, request=self.request) if can_participate else None
        
        # Get business info for the template
        business = giveaway.business
        
        context.update({
            "giveaway": giveaway,
            "business": business,
            "entries_count": entries_count,
            "is_member": is_member_status,
            "is_business": hasattr(user, "business_account") if user.is_authenticated else False,
            "has_joined": has_joined,
            "can_participate": can_participate,
            "entry_form": entry_form,
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user
        if not can_enter_giveaway(user, self.object):
            messages.error(request, "You do not have access to participate in this giveaway.")
            logger.warning(f"Non-member or invalid participation attempt: {user}")
            return redirect(self.object.get_absolute_url())

        form = EntryForm(request.POST, giveaway=self.object, request=request)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = user
            entry.giveaway = self.object
            entry.save()
            messages.success(request, "You are now registered!")
            logger.info(f"User {user} registered for giveaway {self.object} with city {entry.user_location_city}.")
            return redirect(self.object.get_absolute_url())
        else:
            logger.warning(f"Registration failed for user {user} to giveaway {self.object}: {form.errors}")
            context = self.get_context_data()
            context["entry_form"] = form
            return self.render_to_response(context)


class BusinessOnlyMixin(UserPassesTestMixin):
    """Mixin som kun tillater bedriftsbrukere tilgang."""
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and hasattr(user, "business_account")

    def handle_no_permission(self):
        from django.contrib import messages
        messages.error(self.request, "Kun bedrifter kan opprette giveaways.")
        return redirect("accounts:profile")

class GiveawayCreateView(LoginRequiredMixin, BusinessOnlyMixin, CreateView):
    """
    View for å opprette en giveaway for innlogget bedriftsbruker.
    Viser bedriftsnavn og logo i context, og validerer at bruker har business.
    """
    model = Giveaway
    form_class = GiveawayCreateForm
    template_name = "giveaways/giveaway_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["business"] = self.request.user.business_account
        return context

    def form_valid(self, form):
        form.instance.business = self.request.user.business_account
        logger.info(f"Giveaway created for business {form.instance.business.name}")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:business-profile")