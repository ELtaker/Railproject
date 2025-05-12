from django.urls import path
from .views import GiveawayCreateView, GiveawayListView, GiveawayDetailView
from .permissions import is_member, can_enter_giveaway

urlpatterns = [
    path('', GiveawayListView.as_view(), name='list'),
    path('create/', GiveawayCreateView.as_view(), name='create'),
    path('<int:pk>/', GiveawayDetailView.as_view(), name='giveaway_detail'),
]
