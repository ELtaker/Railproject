from .permissions import can_enter_giveaway
from django.contrib.auth.mixins import LoginRequiredMixin
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
    Offentlig oversikt over aktive giveaways. Kan filtreres på sted/postnummer.
    Viser kun aktive giveaways (nå mellom start og slutt).
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
        # Fjern custom kwargs før vi sender til ModelForm
        form_kwargs = {}
        if 'data' in kwargs:
            form_kwargs['data'] = kwargs['data']
        if 'files' in kwargs:
            form_kwargs['files'] = kwargs['files']
        # Disse brukes kun i vår __init__
        form_kwargs['giveaway'] = kwargs['giveaway']
        form_kwargs['request'] = kwargs['request']
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        giveaway = self.get_object()
        user = self.request.user
        entries_count = giveaway.entries.count()
        kan_delta = can_enter_giveaway(user, giveaway)
        entry_form = EntryForm(giveaway=giveaway, request=self.request) if kan_delta else None
        context.update({
            "giveaway": giveaway,
            "entries_count": entries_count,
            "kan_delta": kan_delta,
            "entry_form": entry_form,
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user
        if not can_enter_giveaway(user, self.object):
            messages.error(request, "Du har ikke tilgang til å melde deg på denne giveawayen.")
            logger.warning(f"Ikke-medlem eller ugyldig forsøk på påmelding: {user}")
            return redirect(self.object.get_absolute_url())

        form = EntryForm(request.POST, giveaway=self.object, request=request)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = user
            entry.giveaway = self.object
            entry.save()
            messages.success(request, "Du er nå påmeldt!")
            logger.info(f"Bruker {user} påmeldt giveaway {self.object} med by {entry.user_location_city}.")
            return redirect(self.object.get_absolute_url())
        else:
            logger.warning(f"Påmelding feilet for bruker {user} til giveaway {self.object}: {form.errors}")
            context = self.get_context_data()
            context["entry_form"] = form
            return self.render_to_response(context)


class GiveawayCreateView(LoginRequiredMixin, CreateView):
    """
    View for å opprette en giveaway for innlogget bedriftsbruker.
    Viser bedriftsnavn og logo i context, og validerer at bruker har business.
    """
    model = Giveaway
    form_class = GiveawayCreateForm
    template_name = "giveaways/giveaway_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "business_profile"):
            logger.warning(f"User {request.user} forsøkte å opprette giveaway uten business.")
            return redirect("profile")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["business"] = self.request.user.business_profile
        return context

    def form_valid(self, form):
        form.instance.business = self.request.user.business_profile
        logger.info(f"Giveaway opprettet for business {form.instance.business.name}")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("business_profile")
